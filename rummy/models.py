from django.db import models
import json

class GameTable(models.Model):
    code = models.CharField(max_length=6, unique=True)
    deck_json = models.TextField(null=True, blank=True)
    discard_pile_json = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, default="waiting")
    current_turn = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code

    def get_deck(self):
        return json.loads(self.deck_json) if self.deck_json else []
    
    def set_deck(self, deck):
        self.deck_json = json.dumps(deck)
    
    def get_discard_pile(self):
        return json.loads(self.discard_pile_json) if self.discard_pile_json else []
    
    def set_discard_pile(self, pile):
        self.discard_pile_json = json.dumps(pile)


class Player(models.Model):
    table = models.ForeignKey(GameTable, related_name="players", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    session_id = models.CharField(max_length=100)
    hand_json = models.TextField(null=True, blank=True)
    is_owner = models.BooleanField(default=False)
    position = models.IntegerField(default=0)
    has_drawn = models.BooleanField(default=False)
    score = models.IntegerField(default=0)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.name} ({self.table.code})"
    
    def get_hand(self):
        return json.loads(self.hand_json) if self.hand_json else []
    
    def set_hand(self, hand):
        self.hand_json = json.dumps(hand)
