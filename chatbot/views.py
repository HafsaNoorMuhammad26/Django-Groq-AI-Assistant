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
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001F900-\U0001F9FF"  # supplemental symbols
        u"\U0001FA70-\U0001FAFF"  # symbols extended-a
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text).strip()

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
        
        # Get or create session
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {'history': [], 'mode': mode}
        
        session = chat_sessions[session_id]
        session['mode'] = mode
        
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
        
        # Keep history manageable
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
        
        # ===== FIX: Loop through history properly =====
        # Each message in history has 'user' and 'bot' keys
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
        return JsonResponse({'error': f'JSON export error: {str(e)}'}, status=500)

# ===== CHAT UI =====
def chat_ui(request):
    return render(request, 'chat.html')