from src.narrator import Narrator
from src.recorder import Recorder

if __name__ == "__main__":

    narrator = Narrator()
    recorder = Recorder()
    option = None
    while option != '3':
        print('''
          ################## Spark Reader ##################
          1. Record a book
          2. Narrate a book
          3. Exit program
          ''')
        option = input("\nPlease select an option: ")
        match option:
            case '1':
                recorder.record_book()
            case '2':
                narrator.narrate()
            case _:
                print("Please select a valid option 1, 2, or 3")