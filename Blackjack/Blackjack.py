import random

# Card values for ranks; Ace treated as 11 by default
CARD_VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10, "A": 11
}

def create_deck():
    """Create and shuffle a standard 52-card deck"""
    ranks = list(CARD_VALUES.keys())
    suits = ["♠", "♥", "♦", "♣"]
    deck = [rank + suit for rank in ranks for suit in suits]
    random.shuffle(deck)
    return deck

def calculate_hand_value(hand):
    """
    Calculate best blackjack value for a hand.
    Treat aces as 11 or 1 to get highest value <= 21.
    """
    value = 0
    aces = 0
    for card in hand:
        rank = card[:-1]
        value += CARD_VALUES[rank]
        if rank == "A":
            aces += 1
    # Convert aces from 11 to 1 if bust
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

def is_blackjack(hand):
    """Check if a hand is a blackjack (2 cards adding up to 21)"""
    return len(hand) == 2 and calculate_hand_value(hand) == 21

def display_hand(hand, hide_first_card=False):
    """Display cards; optionally hide dealer's first card"""
    if hide_first_card:
        return "[??] " + " ".join(hand[1:])
    else:
        return " ".join(hand)

def get_bet(balance):
    """Prompt the player for a bet within their balance"""
    while True:
        try:
            bet = int(input(f"You have ${balance}. Enter your bet: $"))
            if 1 <= bet <= balance:
                return bet
            else:
                print(f"Bet must be between $1 and ${balance}.")
        except ValueError:
            print("Please enter a valid number.")

def ask_yes_no(prompt):
    """Prompt player for a yes/no response"""
    while True:
        response = input(prompt + " (Y/N): ").strip().lower()
        if response in ['y', 'n']:
            return response == 'y'
        print("Please enter Y or N.")

def can_split(hand, balance, current_bet):
    """Check if the player can split this hand"""
    return (len(hand) == 2 and
            hand[0][:-1] == hand[1][:-1] and
            balance >= current_bet)

def player_turn(deck, hand, balance, bet, can_double=True, can_split_hand=True):
    """
    Play one player hand: allow hit, stand, double down, split.
    Returns list of resulting hands and bets (due to splits)
    """
    hands = [hand]
    bets = [bet]
    i = 0
    while i < len(hands):
        current_hand = hands[i]
        current_bet = bets[i]
        doubled_down = False

        print(f"\nPlaying hand {i+1}: {display_hand(current_hand)} (Value: {calculate_hand_value(current_hand)})")

        # Check blackjack - skip player turn if blackjack
        if is_blackjack(current_hand):
            print("Blackjack!")
            i += 1
            continue

        while True:
            value = calculate_hand_value(current_hand)

            # Auto bust check
            if value > 21:
                print("Bust!")
                break

            # Build options string based on rules and state
            options = "[H]it, [S]tand"
            if can_double and len(current_hand) == 2 and balance >= current_bet:
                options += ", [D]ouble Down"
            if can_split_hand and can_split(current_hand, balance, current_bet):
                options += ", S[P]lit"

            choice = input(f"Choose action ({options}): ").strip().lower()

            if choice == 'h':
                card = deck.pop()
                current_hand.append(card)
                print(f"You drew {card}. Hand value now {calculate_hand_value(current_hand)}.")
                # After first hit, double down not allowed
                can_double = False
                if calculate_hand_value(current_hand) > 21:
                    print("Bust!")
                    break
            elif choice == 's':
                print(f"Standing with {display_hand(current_hand)} (Value: {calculate_hand_value(current_hand)})")
                break
            elif choice == 'd' and can_double and len(current_hand) == 2 and balance >= current_bet:
                # Double bet, take exactly one card, and stand
                card = deck.pop()
                current_hand.append(card)
                bets[i] *= 2
                balance -= current_bet
                print(f"Double down! Drew {card}. Hand value now {calculate_hand_value(current_hand)}.")
                doubled_down = True
                break
            elif choice == 'p' and can_split_hand and can_split(current_hand, balance, current_bet):
                # Split hand into two hands
                card1 = current_hand[0]
                card2 = current_hand[1]
                # Replace current hand with first split hand + one new card
                hands[i] = [card1, deck.pop()]
                # Add new hand + new card after current
                hands.insert(i + 1, [card2, deck.pop()])
                # Duplicate bet for new hand, deduct from balance
                bets.insert(i + 1, current_bet)
                balance -= current_bet
                print(f"Hand split into two hands:")
                print(f"Hand {i+1}: {display_hand(hands[i])}")
                print(f"Hand {i+2}: {display_hand(hands[i+1])}")
                # Restart this hand turn with new hand
                continue
            else:
                print("Invalid choice or action not allowed.")
                continue
        i += 1

    return hands, bets, balance

def dealer_turn(deck, dealer_hand):
    """Dealer reveals hand and hits until reaching 17 or more (stand on soft 17)"""
    print(f"\nDealer's hand: {display_hand(dealer_hand)} (Value: {calculate_hand_value(dealer_hand)})")
    while True:
        value = calculate_hand_value(dealer_hand)
        # Check if soft 17: value 17 with an ace counted as 11
        soft_17 = (value == 17 and any(card[:-1] == 'A' for card in dealer_hand) and
                   value - 10 <= 17)
        if value < 17 or soft_17:
            card = deck.pop()
            dealer_hand.append(card)
            print(f"Dealer hits and draws {card}. Hand now: {display_hand(dealer_hand)} (Value: {calculate_hand_value(dealer_hand)})")
        else:
            print(f"Dealer stands with {value}.")
            break

def offer_insurance(balance, bet):
    """Offer insurance if dealer's visible card is an Ace"""
    if balance < bet / 2:
        print("Not enough balance for insurance.")
        return False, 0
    want_insurance = ask_yes_no("Dealer shows an Ace. Do you want insurance?")
    if want_insurance:
        insurance_bet = bet // 2
        print(f"Insurance bet placed: ${insurance_bet}")
        return True, insurance_bet
    else:
        return False, 0

def compare_results(hands, bets, dealer_hand, balance, insurance_taken, insurance_bet):
    """Compare player hands with dealer and calculate final balance"""
    dealer_value = calculate_hand_value(dealer_hand)
    dealer_blackjack = is_blackjack(dealer_hand)

    print(f"\nDealer's final hand: {display_hand(dealer_hand)} (Value: {dealer_value})")

    # Handle insurance payout if dealer has blackjack
    if insurance_taken:
        if dealer_blackjack:
            print(f"Dealer has blackjack! Insurance pays 2:1. You win ${insurance_bet * 2} on insurance.")
            balance += insurance_bet * 3  # Return insurance + 2x payout
        else:
            print("Dealer does not have blackjack. You lose insurance bet.")
            balance -= insurance_bet

    # If dealer blackjack and player no blackjack, player loses bets
    if dealer_blackjack:
        for i, hand in enumerate(hands):
            if is_blackjack(hand):
                print(f"Hand {i+1}: Push (both have blackjack). Bet returned: ${bets[i]}")
                balance += bets[i]
            else:
                print(f"Hand {i+1}: Dealer blackjack, you lose bet of ${bets[i]}.")
        return balance

    for i, hand in enumerate(hands):
        player_value = calculate_hand_value(hand)
        print(f"\nYour hand {i+1}: {display_hand(hand)} (Value: {player_value})")

        if is_blackjack(hand):
            # Blackjack pays 3:2
            payout = int(bets[i] * 2.5)
            print(f"Blackjack! You win ${payout}")
            balance += payout
        elif player_value > 21:
            print(f"Bust! You lose bet of ${bets[i]}.")
            # lose bet, nothing to add
        elif dealer_value > 21:
            # Dealer busts, player wins
            payout = bets[i] * 2
            print(f"Dealer busts. You win ${payout}")
            balance += payout
        elif player_value > dealer_value:
            payout = bets[i] * 2
            print(f"You win! You win ${payout}")
            balance += payout
        elif player_value == dealer_value:
            print(f"Push. Bet of ${bets[i]} returned.")
            balance += bets[i]
        else:
            print(f"You lose bet of ${bets[i]}.")
            # lose bet, nothing to add

    return balance

def main():
    print("Welcome to Blackjack!")
    balance = 1000  # starting money

    while balance > 0:
        deck = create_deck()

        bet = get_bet(balance)
        balance -= bet

        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]

        print(f"\nDealer shows: {dealer_hand[1]}")
        print(f"Your hand: {display_hand(player_hand)} (Value: {calculate_hand_value(player_hand)})")

        insurance_taken, insurance_bet = False, 0
        # Offer insurance if dealer's visible card is Ace
        if dealer_hand[1][:-1] == "A":
            insurance_taken, insurance_bet = offer_insurance(balance, bet)
            if insurance_taken:
                balance -= insurance_bet

        # Check immediate blackjack
        player_blackjack = is_blackjack(player_hand)
        dealer_blackjack = is_blackjack(dealer_hand)

        if player_blackjack or dealer_blackjack:
            print(f"\nDealer's hand: {display_hand(dealer_hand)} (Value: {calculate_hand_value(dealer_hand)})")
            if player_blackjack and dealer_blackjack:
                print("Both player and dealer have blackjack. Push.")
                balance += bet  # Return bet
            elif player_blackjack:
                payout = int(bet * 2.5)
                print(f"Blackjack! You win ${payout}")
                balance += payout
            else:
                print("Dealer has blackjack. You lose.")
            # Handle insurance payout if dealer blackjack
            if insurance_taken:
                if dealer_blackjack:
                    print(f"Insurance pays 2:1. You win ${insurance_bet * 2}")
                    balance += insurance_bet * 3
                else:
                    print("You lose insurance bet.")
                    balance -= insurance_bet
            continue

        # Player turn (handles splitting and doubling down)
        hands, bets, balance = player_turn(deck, player_hand, balance, bet)

        # Dealer turn
        dealer_turn(deck, dealer_hand)

        # Compare results and update balance
        balance = compare_results(hands, bets, dealer_hand, balance, insurance_taken, insurance_bet)

        print(f"\nCurrent balance: ${balance}")
        if balance == 0:
            print("You're out of money! Game over.")
            break

        if not ask_yes_no("Play another round?"):
            print("Thanks for playing! Goodbye.")
            break

if __name__ == "__main__":
    main()
