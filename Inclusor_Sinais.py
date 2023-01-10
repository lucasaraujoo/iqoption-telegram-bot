from iqoptionapi.stable_api import IQ_Option
from datetime import datetime, timedelta, date
from colorama import init, Fore, Back
from time import time
from pathlib import Path
import sys
import os
import configparser
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

init(autoreset=True)

ultimo_comando = ''

def configuracao():
    pa = os.path.dirname(os.path.abspath(__file__))
    arquivo = configparser.RawConfigParser()
    config_file = Path(pa + '\\' + 'config.txt').resolve()
    arquivo.read(config_file)

    return {'senha': arquivo.get('GERAL', 'senha'),'email': arquivo.get('GERAL', 'email'), 'telegram_token': arquivo.get('telegram', 'telegram_token'), 'telegram_id': arquivo.get('telegram', 'telegram_id'), 'usar_bot': arquivo.get('telegram', 'usar_bot')}

def start(update, context):
    response_message = "\U0001F47E Estou preparado para enviar sinais. Tenha certeza de que o robot automatizador 24h esteja aberto!"

    bot = context.bot

    bot.send_message(
        chat_id=update.effective_chat.id,
        text=response_message
    )

def sinal(update, context):
    global ultimo_comando 
    
    resposta = '\U0001F4DDAdicione um sinal para a lista no formato (Par | Hora | Tempo | Dir):'
    args = context.args
    if len(args) == 4:    
        resposta = add_sinal(args[1]+'|'+args[2]+'|'+args[0]+'|'+args[3]) 
        resposta = resposta.replace(Fore.YELLOW, '')
        resposta = resposta.replace(Fore.RESET, '')
    else:
        ultimo_comando = 'sinal'
    
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=resposta
    )

def lista(update, context):
    global ultimo_comando 
    lista = []
    resposta = '\U0001F4C7Insira uma lista no formato (Tempo;Par;Horario;Dir):'
    args = context.args
    if len(args) == 4:    
        lista.append(args[0]+';'+args[1]+';'+args[2]+';'+args[3])
        resposta = add_lista(lista)
    else:
        ultimo_comando = 'lista'

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=resposta
    )

def recebe_msg(update, context):
    global ultimo_comando 
    resposta = ''
    lista = []
    message = update.message.text
    if message == '':
        return

    if ultimo_comando == 'sinal':
        message = message.split('\n')
        message = message[0]
        resposta = add_sinal(message)

        resposta = resposta.replace(Fore.YELLOW, '')
        resposta = resposta.replace(Fore.RESET, '')
    elif ultimo_comando == 'lista':
        message = message.replace(" ", "")
        lista = message.split('\n') 
        
        resposta = add_lista(lista)  
    else:
        ultimo_comando = ''
        return

    ultimo_comando = ''  
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=resposta
    )

def add_lista(lista):
    for i, sinal in enumerate(lista):
        if len(sinal.split(';')) != 4 or sinal[0] != 'M':
            return '\u26D4A lista possui um sinal com formato incorreto!'
        if len(sinal.split(';')[1]) != 6 and len(sinal.split(';')[1]) != 10 :
            return '\u26D4Ativo incorreto na lista!'
        if (':' not in sinal.split(';')[2]):
            return '\u26D4Horário incorreto na lista!' 
        if (sinal.split(';')[3] != 'CALL') and (sinal.split(';')[3] != 'PUT'):
            return '\u26D4Sinal na lista com Direção incorreta!'

        if (len(sinal.split(';')[2]) == 5) :
            lista[i] = sinal.split(';')[0]+';'+sinal.split(';')[1]+';'+sinal.split(';')[2]+':00;'+sinal.split(';')[3]
    
    arquivo = open('sinais.txt', 'r')
    conteudo = arquivo.readlines()
    for sinal in lista:
        conteudo.append(sinal+'\n')
    arquivo.close()
    arquivo = open('sinais.txt', 'w')
    arquivo.writelines(conteudo)
    arquivo.close()

    return '\u2705 Lista adicionada.\U0001F4C3'


def add_sinal(novo):
    novo = novo.replace(" ", "")
    novo = novo.split('|')

    if len(novo) < 4:
        return '\u26D4Sinal incompleto!'

    if (len(novo[0]) != 6 and len(novo[0]) != 10) or any(char.isdigit() for char in str(novo[0])):
        return '\u26D4Ativo incorreto!'

    if (':' not in novo[1]):
        return '\u26D4Horário incorreto!'

    if ('M' not in novo[2]):
        return '\u26D4Tempo incorreto!'

    if (novo[3] != 'CALL') and (novo[3] != 'PUT'):
        return '\u26D4Direção incorreta!'

    if len(novo[1]) == 5:
        novo[1] = novo[1]+':00'

    novo = novo[2]+';'+novo[0]+';'+novo[1]+';'+novo[3]

    arquivo = open('sinais.txt', 'r')
    conteudo = arquivo.readlines()
    conteudo.append(novo+'\n')
    arquivo.close()
    arquivo = open('sinais.txt', 'w')
    arquivo.writelines(conteudo)
    arquivo.close()

    return '\u2705 Sinal '+Fore.YELLOW+novo+Fore.RESET+' adicionado.\U0001F4D1'

def main():
    conteudo = []
    config = configuracao()
    telegram_token = config['telegram_token']

    if telegram_token == '':
        input('Insira o Token do Telegram no arquivo de configuração!')
        sys.exit()


    updater = Updater(token=telegram_token)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(
        CommandHandler('start', start)
    )

    dispatcher.add_handler(CommandHandler('sinal', sinal, pass_args = True))

    dispatcher.add_handler(CommandHandler('lista', lista, pass_args = True))

    dispatcher.add_handler(MessageHandler(Filters.text, recebe_msg))

    try:
        updater.start_polling()
        print('Escutando Telegram...')
    except Exception as e:
        print('Erro encontrado: '+str(e)+'\n')
        input()
        sys.exit()

    while True:
        print('\a')
        novo = input('Novo Sinal:')
        
        print(add_sinal(novo))
        


if __name__ == '__main__':
    os.system('cls') 

    print(Fore.GREEN+
    """
    _____           _                            _        _____ _             _  
    |_   _|         | |                          | |      /  ___(_)           (_) 
      | | _ __   ___| |_   _ ___  ___  _ __    __| | ___  \ `--. _ _ __   __ _ _ ___ 
      | || |_ \ / __| | | | / __|/ _ \| |__|  / _` |/ _ \  `--. \ | |_ \ / _` | / __|
     _| || | | | (__| | |_| \__ \ (_) | |    | (_| |  __/ /\__/ / | | | | (_| | \__ |
     \___/_| |_|\___|_|\__,_|___/\___/|_|     \__,_|\___| \____/|_|_| |_|\__,_|_|___/
      """
    )

    print(
    '---------------------------------LUCAS ARAUJO ----------------------------------\n\n'+Fore.RESET+
    '->Inclui sinais na lista em tempo real. Formato de inclusão : PAR|HORA|TEMPO|DIREÇÃO <-\n'
    '')

    main()