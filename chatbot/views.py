from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .utils import generate_response, get_sentiment

# Store chat history (in memory for now)
chat_sessions = {}

@csrf_exempt
def chat(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            session_id = data.get('session_id', 'default')
            mode = data.get('mode', 'legal')
            
            if not user_message:
                return JsonResponse({'error': 'Message cannot be empty'}, status=400)
            
            # Get or create session
            if session_id not in chat_sessions:
                chat_sessions[session_id] = {'history': []}
            
            session = chat_sessions[session_id]
            
            # Generate response
            bot_response = generate_response(
                user_message,
                mode=mode,
                chat_history=session['history']
            )
            
            # Get sentiment
            sentiment_label, _ = get_sentiment(user_message)
            
            # Save to history
            session['history'].append({
                'user': user_message,
                'bot': bot_response
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
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST requests allowed'}, status=405)

def chat_ui(request):
    return render(request, 'chat.html')