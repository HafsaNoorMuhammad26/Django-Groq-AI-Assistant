from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_ui, name='chat_ui'),
    path('pdf-upload/', views.pdf_upload_ui, name='pdf_upload_ui'),
    path('api/chat/', views.chat, name='chat_api'),
    path('api/upload-pdf/', views.upload_and_analyze_pdf, name='upload_pdf'),
    path('api/export/pdf/', views.export_pdf, name='export_pdf'),
    path('api/export/text/', views.export_text, name='export_text'),
    path('api/export/json/', views.export_json, name='export_json'),
]