from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import GameTable, Player
from .game_utils import (
    generate_deck, deal_cards, to_json, from_json,
    check_sequence, check_set, calculate_hand_value
)
import random, string, json

def make_session(request):
    """Create or get session ID"""
    sid = request.session.get("sid")
    if not sid:
        sid = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        request.session["sid"] = sid
    return sid

def example(request):
    """Home page"""
    return render(request, "game.html", {"page": "home"})

def create_table(request):
    """Create a new game table"""
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if not name:
            return render(request, "game.html", {"page": "create", "error": "Name is required"})
        
        sid = make_session(request)
        
        # Generate unique table code
        table_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Create deck and deal cards
        deck = generate_deck()
        hand, rem = deal_cards(deck, 13)
        
        # Create table
        table = GameTable.objects.create(
            code=table_code,
            status="waiting"
        )
        table.set_deck(rem)
        table.set_discard_pile([])
        table.save()
        
        # 👉 IMPORTANT FIX: Save owner's 13 cards properly
        owner = Player.objects.create(
            table=table,
            name=name,
            session_id=sid,
            is_owner=True,
            position=0
        )
        owner.set_hand(hand)
        owner.save()
        
        return redirect("table_screen", code=table_code)
    
    return render(request, "game.html", {"page": "create"})

def join_table(request):
    """Join an existing table"""
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        code = request.POST.get("code", "").upper().strip()
        
        if not name or not code:
            return render(request, "game.html", {
                "page": "join", 
                "error": "Name and code are required"
            })
        
        sid = make_session(request)
        
        try:
            table = GameTable.objects.get(code=code)
        except GameTable.DoesNotExist:
            return render(request, "game.html", {
                "page": "join",
                "error": "Table not found"
            })
        
        # Check if table is full (max 6 players)
        if table.players.count() >= 6:
            return render(request, "game.html", {
                "page": "join",
                "error": "Table is full"
            })
        
        # Check if already joined from this device
        existing = Player.objects.filter(table=table, session_id=sid).first()
        if existing:
            return redirect("table_screen", code=code)
        
        # Deal cards
        deck = table.get_deck()
        if len(deck) < 13:
            return render(request, "game.html", {
                "page": "join",
                "error": "Not enough cards in deck"
            })
        
        hand, rem = deal_cards(deck, 13)
        table.set_deck(rem)
        table.save()
        
        # Create player
        position = table.players.count()
        player = Player.objects.create(
            table=table,
            name=name,
            session_id=sid,
            position=position
        )
        player.set_hand(hand)
        player.save()
        
        return redirect("table_screen", code=code)
    
    return render(request, "game.html", {"page": "join"})

def table_screen(request, code):
    """Main game screen"""
    sid = make_session(request)
    table = get_object_or_404(GameTable, code=code)
    player = Player.objects.filter(table=table, session_id=sid).first()
    
    if not player:
        return redirect("join_table")
    
    hand = player.get_hand()
    players = list(table.players.all())
    
    # Get top discard card
    discard_pile = table.get_discard_pile()
    top_discard = discard_pile[-1] if discard_pile else None
    
    # Check if it's player's turn
    current_player = players[table.current_turn] if players else None
    is_my_turn = current_player and current_player.id == player.id
    
    context = {
        "page": "table",
        "table": table,
        "player": player,
        "players": players,
        "hand": hand,
        "top_discard": top_discard,
        "is_my_turn": is_my_turn,
        "deck_count": len(table.get_deck())
    }
    
    return render(request, "game.html", context)

@require_http_methods(["POST"])
def start_game(request, code):
    """Start the game"""
    sid = make_session(request)
    table = get_object_or_404(GameTable, code=code)
    player = get_object_or_404(Player, table=table, session_id=sid)
    
    if not player.is_owner:
        return JsonResponse({"error": "Only owner can start game"}, status=403)
    
    if table.players.count() < 2:
        return JsonResponse({"error": "Need at least 2 players"}, status=400)
    
    table.status = "playing"
    table.current_turn = 0
    table.save()
    
    return JsonResponse({"success": True})

@require_http_methods(["POST"])
def draw_card(request, code):
    """Draw a card from deck or discard pile"""
    sid = make_session(request)
    table = get_object_or_404(GameTable, code=code)
    player = get_object_or_404(Player, table=table, session_id=sid)
    
    data = json.loads(request.body)
    from_discard = data.get("from_discard", False)
    
    # Check if it's player's turn
    players = list(table.players.all())
    if players[table.current_turn].id != player.id:
        return JsonResponse({"error": "Not your turn"}, status=403)
    
    if player.has_drawn:
        return JsonResponse({"error": "Already drawn this turn"}, status=400)
    
    hand = player.get_hand()
    
    if from_discard:
        discard_pile = table.get_discard_pile()
        if not discard_pile:
            return JsonResponse({"error": "Discard pile is empty"}, status=400)
        card = discard_pile.pop()
        table.set_discard_pile(discard_pile)
    else:
        deck = table.get_deck()
        if not deck:
            return JsonResponse({"error": "Deck is empty"}, status=400)
        card = deck.pop(0)
        table.set_deck(deck)
    
    hand.append(card)
    player.set_hand(hand)
    player.has_drawn = True
    player.save()
    table.save()
    
    return JsonResponse({"success": True, "card": card})

@require_http_methods(["POST"])
def discard_card(request, code):
    """Discard a card"""
    sid = make_session(request)
    table = get_object_or_404(GameTable, code=code)
    player = get_object_or_404(Player, table=table, session_id=sid)
    
    data = json.loads(request.body)
    card = data.get("card")
    
    # Check if player has drawn
    if not player.has_drawn:
        return JsonResponse({"error": "Must draw before discarding"}, status=400)
    
    hand = player.get_hand()
    if card not in hand:
        return JsonResponse({"error": "Card not in hand"}, status=400)
    
    hand.remove(card)
    player.set_hand(hand)
    player.has_drawn = False
    player.save()
    
    # Add to discard pile
    discard_pile = table.get_discard_pile()
    discard_pile.append(card)
    table.set_discard_pile(discard_pile)
    
    # Next player's turn
    players = list(table.players.all())
    table.current_turn = (table.current_turn + 1) % len(players)
    table.save()
    
    return JsonResponse({"success": True})

@require_http_methods(["GET"])
def game_state(request, code):
    """Get current game state"""
    sid = make_session(request)
    table = get_object_or_404(GameTable, code=code)
    player = Player.objects.filter(table=table, session_id=sid).first()
    
    if not player:
        return JsonResponse({"error": "Not in game"}, status=403)
    
    players = list(table.players.all())
    discard_pile = table.get_discard_pile()
    
    players_data = [{
        "id": p.id,
        "name": p.name,
        "card_count": len(p.get_hand()),
        "is_owner": p.is_owner,
        "is_me": p.id == player.id,
        "is_turn": players[table.current_turn].id == p.id if players else False
    } for p in players]
    
    return JsonResponse({
        "status": table.status,
        "current_turn": table.current_turn,
        "deck_count": len(table.get_deck()),
        "top_discard": discard_pile[-1] if discard_pile else None,
        "players": players_data,
        "my_hand": player.get_hand(),
        "has_drawn": player.has_drawn
    })
