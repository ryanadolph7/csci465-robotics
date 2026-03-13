import random
import shlex



class Choice:
    def __init__(self, u, r, a, vs, vr):
        self.user = u
        self.responses = r
        self.actions = a
        self.subChoices = []
        self.variableSet = vs
        self.variableRecall = vr
        if(self.variableSet == True):
            self.variableRecall = False

    def addSubChoice(self, newChoice):
        self.subChoices.append(newChoice)



def matchVar(choice, userEntry):
    userWords = userEntry.split(" ")
    choiceWords = choice.user[0].split(" ")
    varVal = "I don't know"
    varName = None
    #matching the underscore
    if(len(userWords) == len(choiceWords)):
        for word in range(len(choiceWords)):
            if(choiceWords[word] == '_'):
                varVal = userWords[word]
                print(userWords[word])
            elif(choiceWords[word] != userWords[word]):
                return False, ''
    else:
        return False, ''
    #accounts for periods at end of sentences
    if("." in choice.responses[0]):
        responseWords = choice.responses[0].rstrip()[:-1].split(" ")
    else:
        responseWords = choice.responses[0].split(" ")
    responseSentence = ''
    for w in responseWords:
        if(len(w) > 0):
            if(w[0] == "$"):
                varName = w[1:]
                responseSentence += varVal + ' '
            else:
                responseSentence += w + ' '
    return [varName,varVal], responseSentence

def parseText(fileName):
    #dict for definitions
    definitions = {}
    #list for choices
    choices = []
    with open(fileName, 'r') as f:
        scope = 0
        for line in f:
            line = line.lstrip()
            if(len(line) > 0):
                scopeLine = []
                if(line[0] != '#'):
                    error = False
                    #definition
                    if(line[0] == '~'):
                        lineDef = line.split(":")
                        df = lineDef[0][1:]
                        if(len(lineDef) > 1):
                            definitions[tuple(shlex.split(lineDef[1][2:-2]))] = df
                        else:
                            print("Error: Broken definition", line)
                    #choice
                    elif(line[0] == 'u'):
                        varSet = False
                        varRecall = False
                        scopeLine = line.split(':')
                        #uses definition
                        if(scopeLine[1][1] == '~'):
                            userEntry = [scopeLine[1][2:-1]]
                        #uses multiple choices
                        elif (scopeLine[1][1] == '['):
                            userEntry = shlex.split(scopeLine[1][2:-2])
                        #uses one choice (can have variable setting)
                        else:
                            if("_" in scopeLine[1].strip()[1:-1].strip()):
                                varSet = True
                            userEntry = [scopeLine[1].strip()[1:-1].strip()]
                        if(len(scopeLine) > 2):
                            #parsing actions
                            if('<' in scopeLine[2]):
                                actionsAndResponses = scopeLine[2].split(">")[0].split("<")
                                action = actionsAndResponses[1]
                                if("[" in actionsAndResponses[0]):
                                    if("]" in actionsAndResponses[0]):
                                        responses = shlex.split(actionsAndResponses[0][2:-2])
                                    else:
                                        error = True
                                        print("Error: Bad bracket", line)
                                else:
                                    responses = [actionsAndResponses[0]]
                                for r in responses:
                                    #replaces definitions in robot responses
                                    if('~' in r):
                                        r = r.strip()[1:]
                                        for k in definitions.keys():
                                            if(definitions[k] == r):
                                                responses = k
                                    if ('$' in r):
                                        varRecall = True

                            else:
                                action = 'None'
                                if ("[" in scopeLine[2]):
                                    responses = shlex.split(actionsAndResponses[0][2:-2])
                                else:
                                    responses = [scopeLine[2].split("\n")[0]]
                                    for r in responses:
                                        if ('$' in r):
                                            varRecall = True

                        if(not error):
                            if(len(scopeLine[0]) < 2):
                                scope = 0
                                choice = Choice(userEntry, responses, action, varSet, varRecall)
                                tempList = [choice]
                                choices.append(choice)

                            else:
                                newScope = int(scopeLine[0][1])
                                newChoice = Choice(userEntry, responses, action, varSet, varRecall)
                                if(newScope == scope +1):
                                   tempList[len(tempList) - 1].addSubChoice(newChoice)
                                else:
                                    tempList.pop(len(tempList) -1)
                                    tempList[len(tempList) - 1].addSubChoice(newChoice)
                                tempList.append(newChoice)
                                scope = newScope
    return definitions, choices


def interpretText(userInput, d, c, depth, listToChooseFrom, variables):
        returnedText = 'I didnt recognize what you said'
        returnedAction = 'None'
        returnedDepth = depth
        found = False
        actionReturned = False
        #substituting for definitions
        for key in d:
            if(userInput in key):
                userInput = d[key]

        # checking to see if input matches any sub choices
        for choice in listToChooseFrom:
            if (userInput in choice.user):
                returnedDepth += 1
                if (choice.variableSet):
                    varVal, sentence = matchVar(choice, userInput)
                    if (varVal != False):
                        variables[varVal[0]] = varVal[1]
                        returnedText = sentence
                        found = True
                    # checks for variable responses
                if (choice.variableRecall and not found and userInput in choice.user):
                    for r in choice.responses:
                        finalLine = ''
                        if ("." in r):
                            responseWords = r.rstrip(" ")[:-1].split(" ")
                        else:
                            responseWords = r.split(" ")
                        for word in responseWords:
                            if (len(word) > 0):
                                if (word[0] != '$'):
                                    finalLine += word + " "
                                else:
                                    finalLine += variables[word[1:]] + " "
                        returnedText = finalLine
                        found = True
                if (userInput in choice.user and not found):
                    returnedText = random.choice(choice.responses)
                    found = True
                    listToChooseFrom = choice.subChoices

                    # dealing with actions
                if (found and not actionReturned):
                    returnedAction = choice.actions
                    actionReturned = True

                if (found):
                    return returnedText.strip(), returnedAction.strip(), returnedDepth, listToChooseFrom, variables

        if(not found):
            returnedDepth = 0
            #checking to see if input matches any choices in main list
            for choice in c:
                if(choice.variableSet):
                    varVal, sentence = matchVar(choice, userInput)
                    if(varVal != False):
                        variables[varVal[0]] = varVal[1]
                        returnedText = sentence
                        found = True
                    #checks for variable responses
                if(choice.variableRecall and not found and userInput in choice.user):
                    for r in choice.responses:
                        finalLine = ''
                        if ("." in r):
                            responseWords = r.rstrip(" ")[:-1].split(" ")
                        else:
                            responseWords = r.split(" ")
                        for word in responseWords:
                            if (len(word) > 0):
                                if (word[0] != '$'):
                                    finalLine += word + " "
                                else:
                                    finalLine += variables[word[1:]] + " "
                        returnedText = finalLine
                        found = True
                if (userInput in choice.user and not found):
                    returnedText = random.choice(choice.responses)
                    found = True
                    listToChooseFrom = choice.subChoices

                #dealing with actions
                if(found and not actionReturned):
                    returnedAction = choice.actions
                    actionReturned = True

        #depth check
        if(returnedDepth >= 5):
            returnedText = "Error: too deep. Resetting."
            listToChooseFrom = []
        return returnedText.strip(), returnedAction.strip(), returnedDepth, listToChooseFrom, variables

