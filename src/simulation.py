from tqdm   import tqdm
from player import Player

def read_wordlist(filename: str) -> set[str]:
    from pathlib import Path

    path = Path(__file__).parent / "data" / filename

    with path.open() as file:
        initial_words = {
            word[:word.find(',')]
            for word
            in file.readlines()
        }

    return initial_words


def clean_wordlist(initial_words: set[str]) -> set[str]:
    # Normalizing words, replacing accents to their versions with no
    # accents. For example, á, ã, and ç will become a, a, and c. That is a
    # helpful rule only in the Portuguese version of the game.
    import unidecode
    
    initial_words = {
        unidecode.unidecode(word).lower()
        for word
        in initial_words
    }

    # Manually removing words not accepted by term.ooo or palavr.es.
    initial_words.discard('ilson')
    initial_words.discard('louis')
    initial_words.discard('feijo')
    initial_words.discard('haber')
    initial_words.discard('hilma')
    initial_words.discard('havre')
    initial_words.discard('baker')
    initial_words.discard('jader')
    initial_words.discard('zilda')
    initial_words.discard('bayer')
    initial_words.discard('cadmo')
    initial_words.discard('carlo')

    return initial_words


def filter_wordlist(initial_words: set[str], word_length: int) -> set[str]:
    initial_words = {
        word
        for word
        in initial_words
        if len(word) == word_length
    }

    return initial_words


def eval_feedback(word, guess, word_length):
    return ''.join(
        '2' if word[i] == guess[i] else '1' if guess[i] in word else '0'
        for i in range(word_length)
    )


def new_game(word, n_rounds):
    player = Player(len(word), n_rounds)
    guess = player.guess(verbose=False)

    for rounds in range(n_rounds):
        feedback = eval_feedback(word, guess, word_length)
        player.update_words(feedback)

        if feedback == '2' * word_length:
            return True, rounds

        if len(player.possible_answers) == 0:
            return False, rounds

        guess = player.guess(verbose=False)

    return False, n_rounds


word_length = 5
n_rounds    = 6

words = read_wordlist('DELAS_PB.dic')
words = clean_wordlist(words)
words = filter_wordlist(words, word_length)

wins          = 0
wrong_answers = []
distribution  = [0] * n_rounds

for word in tqdm(words):
    result, duration = new_game(word, n_rounds)

    wins += result

    if result: distribution[duration] += 1
    else: wrong_answers += [word]

print("The player loses if the following words are the answer:", wrong_answers)
print(f"Number of victories: {wins} ({wins / len(words):.2%})")
print("Distribution of wins by number of rounds:", distribution)