# coding: utf-8

class App:
    #-----------------------------------------------------------------------------------------------
    #
    #   Print app logo
    #
    #-----------------------------------------------------------------------------------------------
    def print_logo(self):
        print(r'           __ _                        _ _ ')
        print(r'  ___ ____/ _(_)_ __ _____      ____ _| | |')
        print(r" / _ \_  / |_| | '__/ _ \ \ /\ / / _` | | |")
        print(r'|  __// /|  _| | | |  __/\ V  V / (_| | | |')
        print(r' \___/___|_| |_|_|  \___| \_/\_/ \__,_|_|_|')
        print(r'                                           ')



    #-----------------------------------------------------------------------------------------------
    #
    #   Ask a yes/no question, return True if the answer is yes
    #
    #-----------------------------------------------------------------------------------------------
    def confirm(self, question: str) -> bool:
        print(question, end='')

        try:
            answer = input()
        except EOFError:
            raise Exception('no answer received (not running in an interactive terminal?), use --quiet to answer yes automatically')

        return answer.strip().lower() == 'y'
