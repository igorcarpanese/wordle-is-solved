from typing import Any

class Player():
    def __init__(self, word_length: int, n_rounds: int) -> None:
        # Game parameters.
        self.word_length: int  = word_length
        self.n_rounds:    int  = n_rounds
        self.last_round:  bool = False

        # Frequencies the player uses to score words. The
        # self.absolute_frequency_letters contains the frequency of each letter
        # on the language, while self.relative_frequency_letters contains the
        # frequency of each letter as first, second, third... letter of a word
        # for all words on the language.
        self.absolute_frequency_letters: dict[str, float]             = {}
        self.relative_frequency_letters: dict[tuple[str, int], float] = {}

        # List of guessed words.
        self.previous_guesses: list[str] = []

        # List of characters category.
        self.gray_characters:   set[str]              = set()
        self.yellow_characters: set[str]              = set()
        self.green_characters:  set[tuple[int, str]]  = set()

        # Set of words of the language.
        self.initial_words: set[str] = set()

        self.read_wordlist('data/DELAS_PB.dic')
        self.clean_wordlist()
        self.find_absolute_frequency_letters()
        self.filter_wordlist()
        self.find_relative_frequency_letters()

        # Initially, all initial words are possible answers.
        self.possible_answers: set[str] = self.initial_words.copy()


    def read_wordlist(self, filename: str) -> None:
        with open(filename) as file:
            self.initial_words = {
                word[:word.find(',')]
                for word
                in file.readlines()
            }


    def clean_wordlist(self) -> None:
        # Normalizing words, replacing accents to their versions with no
        # accents. For example, á, ã, and ç will become a, a, and c. That is a
        # helpful rule only in the Portuguese version of the game.
        import unidecode
        
        self.initial_words = {
            unidecode.unidecode(word).lower()
            for word
            in self.initial_words
        }

        # Manually removing words not accepted by term.ooo or palavr.es.
        self.initial_words.discard('ilson')
        self.initial_words.discard('louis')
        self.initial_words.discard('feijo')
        self.initial_words.discard('haber')
        self.initial_words.discard('hilma')
        self.initial_words.discard('havre')
        self.initial_words.discard('baker')
        self.initial_words.discard('jader')
        self.initial_words.discard('zilda')
        self.initial_words.discard('bayer')
        self.initial_words.discard('cadmo')
        self.initial_words.discard('carlo')


    def filter_wordlist(self) -> None:
        self.initial_words = {
            word
            for word
            in self.initial_words
            if len(word) == self.word_length
        }


    def find_absolute_frequency_letters(self) -> None:
        from collections import Counter

        frequency = Counter(''.join(self.initial_words))

        # We have different criteria to score the words. It will be easy to
        # merge them if we normalize the frequency between 0 (most rare
        # character) to 1 (most frequent character).
        self.absolute_frequency_letters = self.normalize_frequency(frequency)


    def find_relative_frequency_letters(self) -> None:
        from collections import Counter

        # The player has to consider not only the most frequent characters but
        # also the most common positions of the characters. In Portuguese, for
        # example, there are tons of words that end with -ar, indicating that
        # the word is a verb, so it is okay to assume that the probability of
        # the correct word also ending with -ar is considerable.x
        frequency = Counter([
            (character, index)
            for word in self.initial_words
            for index, character in enumerate(word)
        ])

        # We have different criteria to score the words. It will be easy to
        # merge them if we normalize the frequency between 0 (most rare
        # character+position) to 1 (most frequent character+position).
        self.relative_frequency_letters = self.normalize_frequency(frequency)


    def normalize_frequency(self, frequency: dict[Any, int]) -> dict[Any, float]:
        largest_frequency_value: int = frequency.most_common(1)[0][1]

        normalized_frequency = {
            key: value / largest_frequency_value
            for key, value
            in frequency.items()
        }

        return normalized_frequency


    def score_word(self, word: str) -> float:
        # TODO: We can preprocess criteria0 and criteria1 at the beginning,
        # while criteria2 is modified only after discovering a new green
        # character. Those optimizations would make the player a little bit
        # faster.

        # Give more importance to words with most common characters.
        # Divided by word_length is a penalty for words with duplicated letters.
        # TODO: Think about the general case of that optimization: If there is
        # only one unknown character, the player can repeat letters on the
        # position of the unknown value.
        def criteria0(word: str) -> float:
            return sum(
                self.absolute_frequency_letters[character]
                for character
                in set(word)
            ) / self.word_length
        
        # Give more importance to words with characters in their most
        # common positions.
        # TODO: Try relative frequency of words in self.possible_answers!
        def criteria1(word: str) -> float:
            return sum(
                self.relative_frequency_letters[(character, index)]
                for index, character
                in enumerate(word)
            ) / self.word_length
        

        # Give more importance to words with most unseen characters. An unseen
        # character is a character not guessed before, but it could be at the
        # correct word.
        def criteria2(word: str) -> float:
            unknown_character_positions = set(range(self.word_length)) - {
                index
                for index, _
                in self.green_characters
            }

            unseen_characters = {
                word[unknown_character_position]
                for word in self.possible_answers
                for unknown_character_position in unknown_character_positions
            }

            return len(unseen_characters & set(word)) / self.word_length


        # The general idea is to have different ways to score a word and assign
        # to each way an arbitrary weight. Initially, I had thought the equal
        # weight would be a good idea, but then I realized that the frequency
        # of letters in the position (criteria1) is more relevant at the
        # beginning, and making the weights equal was causing mistakes on the
        # final guesses.
        criteria = [criteria0, criteria1, criteria2]

        # If there are no green characters, or if we are at the last round, it
        # does not make any sense to "give more importance to words with most
        # unseen characters" (criteria2). The player should focus on absolute
        # and relative frequencies, especially the former.
        if len(self.green_characters) == 0 or self.last_round:
            weights = [0.7, 0.3]

        # If there are no yellow characters, the player should focus on
        # exploring words with the most unseen characters.
        elif len(self.yellow_characters) == 0:
            weights = [0.1, 0.0, 0.9]

        # If the player has seen a yellow character, it should focus on
        # figuring out its correct position. To do so, it will mix the
        # different criteria with similar weights.
        else:
            weights = [0.5, 0.2, 0.3]

        return sum(
            weight * criteria(word)
            for weight, criteria
            in zip(weights, criteria)
        )


    def score_words(self, words: str) -> set[tuple[float, str]]:
        return {
            (self.score_word(word), word)
            for word
            in words
        }


    def guess(self, feedback: str = "", verbose: bool = True) -> str:
        if len(self.possible_answers) == 1:
            guess: str = self.possible_answers.pop()

            if verbose:
                print(f"{guess} (that is the only possible answer)")

            return guess

        self.last_round = len(self.previous_guesses) == self.n_rounds - 1

        # If we are not at the last round and there are no yellow characters,
        # we should explore as many unseen characters as possible. Note that we
        # will not try to win on this round.
        if not self.last_round and len(self.yellow_characters) == 0:
            wordlist = self.initial_words

        # If we are at the last round, we should guess the word with the
        # highest score in the set of possible answers. If there is at least
        # one yellow character, we will try to find its correct position using
        # only the possible answers. In both ways, we will use
        # self.possible_answers.
        else:
            wordlist = self.possible_answers

        scores: set[tuple[float, str]] = self.score_words(wordlist)
        guess:  str                    = sorted(scores, reverse=True)[0][1]

        if verbose:
            print(f"{guess} ({len(self.possible_answers)} possible answers)")

        self.previous_guesses += [guess]

        return guess


    def update_words(self, feedback: str) -> None:
        def update_gray_characters(feedback: str) -> None:
            self.gray_characters |= {
                    self.previous_guesses[-1][index]
                    for index, character
                    in enumerate(feedback)
                    if character == '0'
                }


        def update_yellow_characters(feedback: str) -> None:
            self.yellow_characters |= {
                self.previous_guesses[-1][index]
                for index, character
                in enumerate(feedback)
                if character == '1'
            }


        def update_green_characters(feedback: str) -> None:
            self.green_characters |= {
                (index, self.previous_guesses[-1][index])
                for index, hit
                in enumerate(feedback)
                if hit == '2'
            }

            # Optimization: If all possible answers have the same character in
            # the same position, then that character is green. Also, note that
            # if self.green_characters == 0, the player did not hit any
            # character. Consequentially, it does not make any sense to try
            # that optimization for all initial words.
            if len(self.green_characters) > 0:
                new_green_characters = set()

                for index in range(self.word_length):
                    characters_at_position_index = {
                        word[index]
                        for word
                        in self.possible_answers
                    }

                    if len(characters_at_position_index) == 1:
                        new_green_characters |= {(
                            index,
                            list(self.possible_answers)[0][index]
                        )}

                self.green_characters |= new_green_characters

            # Every time a green character appears, the set of yellow
            # characters might have to be updated because a yellow
            # character that becomes green loses the yellow status.
            if len(self.green_characters) > 0:
                self.yellow_characters -= {
                    character
                    for _, character
                    in self.green_characters
                }



        # The player keeps the list of gray characters because, typically, it
        # will guess words without them. Exception: If no yellow character on
        # the guessing words with gray characters might give us information
        # about unseen characters.
        def remove_gray_characters() -> set[str]:
            self.possible_answers = {
                word
                for word in self.possible_answers
                if not any(
                    character in word
                    for character
                    in self.gray_characters
                )
            }

        # If the player knows that a character is on the correct word but does
        # not know its position, it should keep using it until the yellow
        # character becomes green. To do that, we have to force all possible
        # answers to have yellow characters.
        def force_yellow_characters() -> set[str]:
            self.possible_answers = {
                word
                for word in self.possible_answers
                if all(
                    character in word
                    for character
                    in self.yellow_characters
                )
            }

        # If a yellow character appears, the player knows that its correct
        # position is not its current position.
        def remove_yellow_characters_wrong_position(feedback: str) -> set[str]:
            yellow_character_positions_last_guess: list[int] = {
                index
                for index, hit
                in enumerate(feedback)
                if hit == '1'
            }

            filtered_words = self.possible_answers.copy()

            for index in yellow_character_positions_last_guess:
                yellow_character_last_guess = self.previous_guesses[-1][index]

                filtered_words = {
                    word
                    for word
                    in filtered_words
                    if word[index] != yellow_character_last_guess
                }

            self.possible_answers = filtered_words.copy()

        # If a green character appears, the player knows its correct position.
        def force_green_characters(feedback: str) -> set[str]:
            green_character_positions_last_guess: list[int] = {
                index
                for index, hit
                in enumerate(feedback)
                if hit == '2'
            }

            filtered_words = self.possible_answers.copy()

            for index in green_character_positions_last_guess:
                green_character_last_guess = self.previous_guesses[-1][index]

                filtered_words = {
                    word
                    for word
                    in filtered_words
                    if word[index] == green_character_last_guess
                }

            self.possible_answers = filtered_words.copy()


        update_gray_characters(feedback)
        update_yellow_characters(feedback)

        # Remove the previous guess from self.initial_words because, of course,
        # it does not make any sense to guess a word previously guessed. The
        # following rules guarantee the removal of the previous guess from
        # self.possible_answers.
        self.initial_words.discard(self.previous_guesses[-1])

        remove_gray_characters()
        force_yellow_characters()
        remove_yellow_characters_wrong_position(feedback)        
        force_green_characters(feedback)

        # We have to update the green characters at the end because the state
        # of self.possible_answers might affect it.
        update_green_characters(feedback)