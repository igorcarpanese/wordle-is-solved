from player import Player

def play(word_length, n_rounds):
    player = Player(word_length, n_rounds)

    player.guess()

    for _ in range(n_rounds-1):
        feedback = input()

        if feedback == '2' * word_length:
            print("You win! :-)")
            exit(0)

        player.update_words(feedback)

        if len(player.possible_answers) == 0:
            print("There are no more words in the set of possible answers. You lose! :-(")
            exit(0)

        player.guess(feedback)

    feedback = input()

    if feedback != '2' * word_length:
        print("You lose! :-(")
    else:
        print("You win! :-)")


if __name__ == '__main__':
    word_length = 5
    n_rounds = 6

    play(word_length, n_rounds)