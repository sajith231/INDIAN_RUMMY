from django.urls import path
from . import views

urlpatterns = [
    # Page views
    path('', views.example, name='home'),
    path('create/', views.create_table, name='create_table'),
    path('join/', views.join_table, name='join_table'),
    path('table/<str:code>/', views.table_screen, name='table_screen'),
    
    # API endpoints
    path('api/table/<str:code>/start/', views.start_game, name='start_game'),
    path('api/table/<str:code>/draw/', views.draw_card, name='draw_card'),
    path('api/table/<str:code>/discard/', views.discard_card, name='discard_card'),
    path('api/table/<str:code>/state/', views.game_state, name='game_state'),
    path('api/table/<str:code>/declare/', views.declare, name='declare'),
]
