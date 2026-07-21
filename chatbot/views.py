from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import re
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .utils import generate_response, get_sentiment
import PyPDF2
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import time  # ✅ NEW: For session expiry
import sentry_sdk  # ✅ NEW: For error tracking

# Store chat sessions (in-memory for development)
chat_sessions = {}

# ===== HELPER: Remove Emojis for PDF =====
def remove_emojis(text):
    """Remove emojis and special characters for PDF export"""
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols 
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"   # dingbats
        u"\U000024C2-\U0001F251"   # enclosed characters
        u"\U0001F900-\U0001F9FF"   # supplemental symbols 
        u"\U0001FA70-\U0001FAFF"   # symbols extended-a 
        u"\U00002600-\U000026FF"   # misc symbols (☀-⛿)  #  NEW
        u"\U00002B50-\U00002BFF"   # star/arrows (⭐-⯿)  #  NEW
        u"\U000000A9-\U000000AE"   # copyright/trademark (©-®)  #  NEW
        "]+",
        flags=re.UNICODE
    )
    
    #  Handle common problematic characters
    text = text.replace('•', '-')      # bullet points
    text = text.replace('★', '*')      # star
    text = text.replace('☆', '*')      # star
    text = text.replace('◆', '-')      # diamond
    text = text.replace('◇', '-')      # diamond
    text = text.replace('→', '->')     # arrow
    text = text.replace('←', '<-')     # arrow
    text = text.replace('↑', '^')      # arrow
    text = text.replace('↓', 'v')      # arrow
    text = text.replace('✓', '[X]')    # checkmark
    text = text.replace('✔', '[X]')    # checkmark
    text = text.replace('✗', '[ ]')    # cross
    text = text.replace('✘', '[ ]')    # cross
    text = text.replace('…', '...')    # ellipsis
    
    return emoji_pattern.sub(r'', text).strip()

# ===== CLEANUP FUNCTION =====
def cleanup_old_sessions():
    """Remove expired sessions to prevent memory leaks"""
    current_time = time.time()
    
    # 1. Remove sessions older than 1 hour (3600 seconds)
    expired_sessions = [
        sid for sid, session in chat_sessions.items()
        if current_time - session.get('last_accessed', 0) > 3600
    ]
    for sid in expired_sessions:
        del chat_sessions[sid]
    
    # 2. If still too many sessions, keep only 100 most recent
    if len(chat_sessions) > 100:
        # Sort by last_accessed and keep 100 most recent
        sorted_sessions = sorted(
            chat_sessions.items(),
            key=lambda x: x[1].get('last_accessed', 0),
            reverse=True
        )
        # Keep only first 100
        sessions_to_keep = dict(sorted_sessions[:100])
        # Clear and update
        chat_sessions.clear()
        chat_sessions.update(sessions_to_keep)

# ===== PDF UPLOAD & ANALYSIS =====
def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return None

@csrf_exempt
@require_http_methods(["POST"])
def upload_and_analyze_pdf(request):
    try:
        if 'pdf_file' not in request.FILES:
            return JsonResponse({'error': 'No PDF file uploaded'}, status=400)

        pdf_file = request.FILES['pdf_file']

        if pdf_file.size > 10 * 1024 * 1024:
            return JsonResponse({'error': 'File too large. Max size is 10MB.'}, status=400)

        if not pdf_file.name.endswith('.pdf'):
            return JsonResponse({'error': 'Only PDF files are supported'}, status=400)

        #  EXTRACTION: Use helper function (single extraction)
        text = extract_text_from_pdf(pdf_file)

        if not text:
            return JsonResponse({'error': 'Could not extract text from PDF.'}, status=400)

        # Limit text
        if len(text) > 10000:
            text = text[:10000] + "... [truncated]"

        # Get session ID
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id', 'default')
        except:
            session_id = 'default'

        # ✅ NEW: Cleanup old sessions
        cleanup_old_sessions()

        if session_id not in chat_sessions:
            chat_sessions[session_id] = {
                'history': [],
                'mode': 'legal',
                'last_accessed': time.time()  # ✅ NEW
            }

        session = chat_sessions[session_id]
        session['last_accessed'] = time.time()  # ✅ NEW

        # Generate analysis
        analysis_prompt = f"""
        You are a Legal Document Analyst. Analyze the following legal document and provide:

        1. **Document Summary** (2-3 sentences)
        2. **Key Clauses** (list the most important clauses)
        3. **Potential Issues** (any concerning clauses or ambiguities)
        4. **Plain English Explanation** (explain the document in simple terms)

        Document:
        {text}
        """

        analysis_response = generate_response(analysis_prompt, mode='legal', chat_history=session['history'])

        session['history'].append({
            'user': f"[PDF Upload] {pdf_file.name}",
            'bot': analysis_response,
            'sentiment': 'NEUTRAL'
        })

        # ✅ NEW: Limit history per session
        if len(session['history']) > 20:
            session['history'] = session['history'][-20:]

        return JsonResponse({
            'analysis': analysis_response,
            'filename': pdf_file.name,
            'success': True
        })

    except Exception as e:
        sentry_sdk.capture_exception(e)  # ✅ NEW: Send to Sentry
        return JsonResponse({'error': f'Analysis error: {str(e)}'}, status=500)
    
# ===== PDF UPLOAD UI =====
def pdf_upload_ui(request):
    return render(request, 'pdf_upload.html')

# ===== API CHAT ENDPOINT =====
@csrf_exempt
@require_http_methods(["POST"])
def chat(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        mode = data.get('mode', 'legal')
        
        if not user_message:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        # ✅ NEW: Cleanup old sessions
        cleanup_old_sessions()
        
        # Get or create session with last_accessed
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {
                'history': [],
                'mode': mode,
                'last_accessed': time.time()  # ✅ NEW
            }
        
        session = chat_sessions[session_id]
        session['mode'] = mode
        session['last_accessed'] = time.time()  # ✅ NEW: Update timestamp
        
        # Get sentiment
        sentiment_label, sentiment_score = get_sentiment(user_message)
        
        # Generate response
        bot_response = generate_response(
            user_message,
            mode=mode,
            chat_history=session['history']
        )
        
        # Save to history
        session['history'].append({
            'user': user_message,
            'bot': bot_response,
            'sentiment': sentiment_label
        })
        
        # Keep history manageable (max 20 messages)
        if len(session['history']) > 20:
            session['history'] = session['history'][-20:]
        
        return JsonResponse({
            'response': bot_response,
            'sentiment': sentiment_label,
            'mode': mode
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        sentry_sdk.capture_exception(e)  # ✅ NEW: Send to Sentry
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

# ===== PDF EXPORT ENDPOINT =====
@csrf_exempt
@require_http_methods(["POST"])
def export_pdf(request):
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', 'default')
        
        if session_id not in chat_sessions:
            return JsonResponse({'error': 'No chat history found'}, status=404)
        
        session = chat_sessions[session_id]
        history = session['history']
        
        if not history:
            return JsonResponse({'error': 'No messages to export'}, status=400)
        
        # ✅ NEW: Update last_accessed
        session['last_accessed'] = time.time()
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20,
        )
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=13,
            alignment=TA_LEFT,
            spaceAfter=6,
            textColor='#1a2a6c',
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_LEFT,
            spaceAfter=10,
            leftIndent=10,
        )
        date_style = ParagraphStyle(
            'CustomDate',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor='#666666',
            spaceAfter=20,
        )
        footer_style = ParagraphStyle(
            'CustomFooter',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor='#999999',
            spaceAfter=6,
        )
        
        # Build content
        content = []
        
        # Title
        content.append(Paragraph("⚖️ Legal & 🌿 Wellness AI - Chat Export", title_style))
        content.append(Spacer(1, 0.1 * inch))
        
        # Date
        date_str = datetime.now().strftime('%Y-%m-%d %I:%M %p')
        content.append(Paragraph(f"Exported on: {date_str}", date_style))
        content.append(Spacer(1, 0.2 * inch))
        
        # Loop through history
        for idx, msg in enumerate(history):
            # User message
            user_text = msg.get('user', '')
            if user_text:
                content.append(Paragraph("👤 <b>User:</b>", header_style))
                clean_user = remove_emojis(user_text)
                content.append(Paragraph(clean_user, body_style))
                content.append(Spacer(1, 0.05 * inch))
            
            # Bot response
            bot_text = msg.get('bot', '')
            if bot_text:
                content.append(Paragraph("🤖 <b>Assistant:</b>", header_style))
                clean_bot = remove_emojis(bot_text)
                content.append(Paragraph(clean_bot, body_style))
                content.append(Spacer(1, 0.1 * inch))
            
            # Add a separator line between exchanges
            if idx < len(history) - 1:
                content.append(Paragraph("-" * 60, footer_style))
                content.append(Spacer(1, 0.1 * inch))
        
        # Footer
        content.append(Spacer(1, 0.3 * inch))
        content.append(Paragraph("=" * 60, footer_style))
        content.append(Paragraph("For professional advice, consult a licensed professional.", footer_style))
        content.append(Paragraph(f"Exported from Legal & Wellness AI Assistant", footer_style))
        content.append(Paragraph(f"Total messages: {len(history)}", footer_style))
        
        # Build PDF
        doc.build(content)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="chat_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        response.write(pdf_data)
        return response
        
    except Exception as e:
        sentry_sdk.capture_exception(e)  # ✅ NEW: Send to Sentry
        return JsonResponse({'error': f'PDF generation error: {str(e)}'}, status=500)

# ===== TEXT EXPORT ENDPOINT =====
@csrf_exempt
@require_http_methods(["POST"])
def export_text(request):
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', 'default')
        
        if session_id not in chat_sessions:
            return JsonResponse({'error': 'No chat history found'}, status=404)
        
        session = chat_sessions[session_id]
        history = session['history']
        
        if not history:
            return JsonResponse({'error': 'No messages to export'}, status=400)
        
        # ✅ NEW: Update last_accessed
        session['last_accessed'] = time.time()
        
        # Build text content
        lines = []
        lines.append("=" * 60)
        lines.append("⚖️ Legal & 🌿 Wellness AI - Chat Export")
        lines.append(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
        lines.append("=" * 60)
        lines.append("")
        
        for idx, msg in enumerate(history):
            user_msg = msg.get('user', '')
            bot_msg = msg.get('bot', '')
            
            lines.append(f"👤 User: {user_msg}")
            lines.append("")
            lines.append(f"🤖 Assistant: {bot_msg}")
            lines.append("")
            lines.append("-" * 40)
            lines.append("")
        
        lines.append("=" * 60)
        lines.append("End of conversation")
        lines.append(f"Total messages: {len(history)}")
        lines.append("")
        lines.append("For professional advice, consult a licensed professional.")
        
        text_data = "\n".join(lines)
        
        response = HttpResponse(text_data, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="chat_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt"'
        return response
        
    except Exception as e:
        sentry_sdk.capture_exception(e)  # ✅ NEW: Send to Sentry
        return JsonResponse({'error': f'Text export error: {str(e)}'}, status=500)

# ===== JSON EXPORT ENDPOINT =====
@csrf_exempt
@require_http_methods(["POST"])
def export_json(request):
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', 'default')
        
        if session_id not in chat_sessions:
            return JsonResponse({'error': 'No chat history found'}, status=404)
        
        session = chat_sessions[session_id]
        history = session['history']
        
        if not history:
            return JsonResponse({'error': 'No messages to export'}, status=400)
        
        # ✅ NEW: Update last_accessed
        session['last_accessed'] = time.time()
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "session_id": session_id,
            "messages": history
        }
        
        json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        response = HttpResponse(json_data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="chat_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
        return response
        
    except Exception as e:
        sentry_sdk.capture_exception(e)  # ✅ NEW: Send to Sentry
        return JsonResponse({'error': f'JSON export error: {str(e)}'}, status=500)

# ===== CHAT UI =====
def chat_ui(request):
    return render(request, 'chat.html')


# ===== TEST SENTRY ENDPOINT (Temporary) =====
# from django.http import HttpResponse
# def test_sentry(request):
#     x = 1 / 0
#     return HttpResponse("This won't run")