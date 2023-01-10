from iqoptionapi.stable_api import IQ_Option
from datetime import datetime
from dateutil import tz
from getpass import getpass
from colorama import init, Fore, Back
import warnings
import time
import json, requests
import logging
import configparser
from pathlib import Path
import sys
import os
from threading import Thread, Lock
lock = Lock()
warnings.filterwarnings("ignore", category=UserWarning)

"""pa = os.path.dirname(os.path.abspath(__file__))
arquivo = configparser.RawConfigParser()
config_file = Path(pa + '\\' + 'config.txt').resolve()
print(config_file)"""
logging.disable(level=(logging.DEBUG))

def GravaLog(sinal, resultado):
    arquivo_log = open('logs\log_' + str((datetime.now()).strftime('%Y-%m-%d')) + '.txt', 'a')
    arquivo_log.write(sinal+'- '+resultado.upper()+'\n')
    arquivo_log.close()

def Martingale(valor):
    valorGale = float(config['valorGale'])
    lucro_esperado = float(valor) * valorGale

    return float(lucro_esperado)


def Payout(par, timeframe):
    API.subscribe_strike_list(par, timeframe)
    while True:
        d = API.get_digital_current_profit(par, timeframe)
        if d > 0:
            break
        time.sleep(1)
    API.unsubscribe_strike_list(par, timeframe)
    return float(d / 100)


def banca():
    return API.get_balance()


def configuracao():
    pa = os.path.dirname(os.path.abspath(__file__))
    arquivo = configparser.RawConfigParser()
    config_file = Path(pa + '\\' + 'config.txt').resolve()
    arquivo.read(config_file)

    return {'senha': arquivo.get('GERAL', 'senha'),'email': arquivo.get('GERAL', 'email'),'entrada': arquivo.get('GERAL', 'entrada'), 'conta': arquivo.get('GERAL', 'conta'), 'stop_win': arquivo.get('GERAL', 'stop_win'), 'stop_loss': arquivo.get('GERAL', 'stop_loss'), 'payout': 0, 'banca_inicial': 0, 'martingale': arquivo.get('GERAL', 'martingale'), 'valorGale': arquivo.get('GERAL', 'valorGale'), 'sorosgale': arquivo.get('GERAL', 'sorosgale'), 'niveis': arquivo.get('GERAL', 'niveis'), 'analisarTendencia': arquivo.get('GERAL', 'analisarTendencia'), 'noticias': arquivo.get('GERAL', 'noticias'), 'telegram_token': arquivo.get('telegram', 'telegram_token'), 'telegram_id': arquivo.get('telegram', 'telegram_id'), 'usar_bot': arquivo.get('telegram', 'usar_bot')}


def carregaSinais():
    pa = os.path.dirname(os.path.abspath(__file__))
    x = open(pa + '\\' + 'sinais.txt')
    y = []
    for i in x.readlines():
        y.append(i)
    y.sort(key=lambda item: datetime.strptime(item.split(";")[2], "%H:%M:%S"))
    x.close()
    #apaga o conteudo para aguardar mais sinais ao vivo
    if len(y) > 0:
        x = open(pa + '\\' + 'sinais.txt', 'w')
        x.close()
    
    if len(y) == 1:
        Mensagem('\n\n\U0001F6A6'+str(len(y))+' sinal encontrado na lista.\n')
    elif len(y) > 0:
        Mensagem('\n\n\U0001F6A6'+str(len(y))+' sinais encontrados na lista.\n')

    return y

stop_loss = False
stop_win = False
lucroTotal = 0
def entradas(par, entrada, direcao, config, opcao, timeframe):
    global stop_loss, stop_win, lucroTotal
    if opcao == 'digital':
        status, id = API.buy_digital_spot(par, entrada, direcao, timeframe)
        if status:
            
            while True:
                status, lucro = API.check_win_digital_v2(id)
                #print(API.check_win_digital_v2(id))
                if status:
                    # STOP WIN/STP LOSS

                    banca_att = banca()
                    stop_loss = False
                    stop_win = False

                    #if round((banca_att - float(config['banca_inicial'])), 2) <= (abs(float(config['stop_loss'])) * -1.0):
                    if round((lucroTotal + lucro), 2) <= (abs(float(config['stop_loss'])) * -1.0):
                        stop_loss = True

                    #if round((banca_att - float(config['banca_inicial'])), 2) >= abs(float(config['stop_win'])):
                    if round((lucroTotal + lucro), 2) >= abs(float(config['stop_win'])):
                        stop_win = True


                    if lucro > 0:
                        return 'win', round(lucro, 2), stop_win
                    elif lucro == 0.0:
                        return 'doji', 0, False
                    else:
                        return 'loss', round(lucro, 2), stop_loss
                    break
        else:
            return 'error', 0, False

    elif opcao == 'binaria':
        status, id = API.buy(entrada, par, direcao, timeframe)

        if status:
            resultado, lucro = API.check_win_v4(id)
            #print(API.check_win_v3(id))

            banca_att = banca()
            stop_loss = False
            stop_win = False

            if round((lucroTotal + lucro), 2) <= (abs(float(config['stop_loss'])) * -1.0):
                stop_loss = True

            if round((lucroTotal + lucro), 2) >= abs(float(config['stop_win'])):
                stop_win = True

            if resultado:
                if resultado == 'win':
                    return resultado, round(lucro, 2), stop_win
                elif resultado == 'equal':
                    return 'doji', 0, False
                elif resultado == 'loose':
                    return 'loss', round(lucro, 2), stop_loss
        else:
            return 'error', 0, False
    else:
        return 'opcao errado', 0, False


def timestamp_converter():
    hora = datetime.now()
    tm = tz.gettz('America/Sao_Paulo')
    hora_atual = hora.astimezone(tm)
    return hora_atual.strftime('%H:%M:%S')

def Timeframe(timeframe):

    if timeframe == 'M1':
        return 1

    elif timeframe == 'M5':
        return 5

    elif timeframe == 'M15':
        return 15

    elif timeframe == 'M30':
        return 30

    elif timeframe == 'H1':
        return 60
    else:
        return 'erro'


def Mensagem(mensagem):
    print(mensagem)
    if VERIFICA_BOT == 'S':
        thread_tel = Thread(target=mensagem_telegram, args=(mensagem,))
        thread_tel.start()
        
msg_fila = 0

def mensagem_telegram(msg):
    global msg_fila
    token = config['telegram_token']
    chatID = TELEGRAM_ID
    #RETIRA AS CORES E COLOCA EMOJIS
    msg = msg.replace(Fore.RED, '\u274c ') #x
    msg = msg.replace(Fore.YELLOW, '\U0001F413 ') #galo
    msg = msg.replace(Fore.GREEN, '\u2705 ') #check
    msg = msg.replace(Fore.RESET, '')

    send = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chatID}&parse_mode=Markdown&text={msg}'
    try:
        msg_fila += 1
        time.sleep((0.1)*(msg_fila*msg_fila))
        requests.get(send)  
    except Exception as e:
        print('\nErro ao enviar mensagem para o robot no Telegram (Erro:'+str(e)+')\n')  
    
    msg_fila -= 1

def tendencia(par, timeframe):
    velas = API.get_candles(par, (int(timeframe) * 60), 12,  time.time())
    ultimo = round(velas[0]['close'], 6)
    primeiro = round(velas[-1]['close'], 6)
    diferenca = abs(round(((ultimo - primeiro) / primeiro) * 100, 3))
    tendencia = "call" if ultimo < primeiro and diferenca > 0.01 else "put" if ultimo > primeiro and diferenca > 0.01 else False
    return tendencia

def checkProfit(par, timeframe):
    all_asset = API.get_all_open_time()
    profit = API.get_all_profit()

    digital = 0
    binaria = 0

    if timeframe == 60:
        return 'binaria'

    if all_asset['digital'][par]['open']:
        digital = Payout(par, timeframe)
        digital = round(digital, 2)

    if all_asset['turbo'][par]['open']:
        binaria = round(profit[par]["turbo"], 2)

    if binaria < digital:
        return "digital"

    elif digital < binaria:
        return "binaria"

    elif digital == binaria:
        return "binaria"

    else:
        "erro"

def noticas(paridade, minutos_lista):
    objeto = json.loads(texto)

    # Verifica se o status code é 200 de sucesso
    if response.status_code != 200 or objeto['success'] != True:
        print('Erro ao contatar notícias')

    # Pega a data atual
    data = datetime.now()
    tm = tz.gettz('America/Sao_Paulo')
    data_atual = data.astimezone(tm)
    data_atual = data_atual.strftime('%Y-%m-%d')

    # Varre todos o result do JSON
    for noticia in objeto['result']:
        # Separa a paridade em duas Ex: AUDUSD separa AUD e USD para comparar os dois
        paridade1 = paridade[0:3]
        paridade2 = paridade[3:6]
        
        # Pega a paridade, impacto e separa a data da hora da API
        moeda = noticia['economy']
        impacto = noticia['impact']
        atual = noticia['data']
        data = atual.split(' ')[0]
        hora = atual.split(' ')[1]
        
        # Verifica se a paridade existe da noticia e se está na data atual
        if moeda == paridade1 or moeda == paridade2 and data == data_atual:
            formato = '%H:%M:%S'
            d1 = datetime.strptime(hora, formato)
            d2 = datetime.strptime(minutos_lista, formato)
            dif = (d1 - d2).total_seconds()
            # Verifica a diferença entre a hora da noticia e a hora da operação
            minutesDiff = dif / 60
        
            # Verifica se a noticia irá acontencer 30 min antes ou depois da operação
            if minutesDiff >= -30 and minutesDiff <= 0 or minutesDiff <= 30 and minutesDiff >= 0:
                return impacto, moeda, hora, True
         
       
    return 0, 0, 0, False

print(""" 
        Automatizador de sinais ao vivo para iqoption
        ___    ___    _____       ___   ___   ___   ___ 
        | _ )  / _ \  |_   _|     | __| | _ \ | __| | __|
        | _ \ | (_) |   | |       | _|  |   / | _|  | _| 
        |___/  \___/    |_|       |_|   |_|_\ |___| |___|
                                                        
        Para sinais 24h - versão - 1.4.5 - Lucas Araújo
        Créditos: Baby AutoBot
        

""")
config = configuracao()
email = config['email']
senha = config['senha']
API = IQ_Option(email, senha)
API.connect()

API.change_balance(config['conta'])  # PRACTICE / REAL

global VERIFICA_BOT, TELEGRAM_ID

config['banca_inicial'] = banca()

VERIFICA_BOT = config['usar_bot']
TELEGRAM_ID = config['telegram_id']
analisarTendencia = config['analisarTendencia']
noticias = config['noticias']

if API.check_connect():
    os.system('cls') 
    Mensagem('\U0001F916 Conectado com sucesso no AutoBot24H como '+ email+ '!')
    if noticias == 'S':
        response = requests.get("https://botpro.com.br/calendario-economico/")
        texto = response.content
else:
    print(' Erro ao conectar')
    input('\n\n Aperte enter para sair')
    sys.exit()

valor_entrada = config['entrada']
valor_entrada_b = float(valor_entrada)

lucro = 0


sinais = carregaSinais()
global start_bot
start_bot = 0
def Operar(timeframe_retorno,timeframe, par, minutos_lista, direcao):
    global noticas, analisarTendencia, valor_entrada_b, lucro, lucroTotal, start_bot, sinais
    opcao = 'error'
    #linha com o sinal para gravar no log
    linha_log = 'M'+str(timeframe)+';'+par+';'+str(minutos_lista)+';'+direcao.upper()+' '
    # print(par)
    verf = False
    while True:
        t = timestamp_converter()
        s = minutos_lista
        f = '%H:%M:%S'
        dif = abs((datetime.strptime(t, f) - datetime.strptime(s, f)).total_seconds())
        # print('Agora: ',t)
        # print('Falta: ',dif)

        # Verifica se tem noticias 40 seg antes
        if noticias == 'S':
            if dif == 40:
                impacto, moeda, hora, stts = noticas(par,minutos_lista)
                if stts:
                    if impacto > 1:
                        Mensagem(f' \U0001f4f0NOTÍCIA DE {impacto} TOUROS\U0001f402 NA MOEDA {moeda} ÀS {hora}!')
                        GravaLog(linha_log, 'NEWS')
                        break

        # Verifica opção binário ou digita quando falta 25 seg
        if dif == 25:
            opcao = checkProfit(par, timeframe)

        # Verifica tendencia quando falta 5 seg
        if analisarTendencia == 'S':
            if dif == 5:
                if verf == False:
                    tend = tendencia(par, timeframe)
                    verf = True
                    if tend == False:
                        Mensagem(f'\U0001f4ca Ativo {par} com tendência de lateralização!\U0001F4B9')
                        GravaLog(linha_log, 'TENDENCIA LATERAL')
                    else:
                        if tend != direcao:
                            Mensagem(f'\n\U0001f6ab Ativo {par} contra tendência!\U0001F4C8\n')
                            GravaLog(linha_log, 'CONTRA TENDENCIA')
                            break

        #Inicia a operação 2 seg antes
        entrar = True if (dif == 2) else False

        if entrar:
            Mensagem('\n\n \U0001F3F9 INICIANDO OPERAÇÃO \U0001f3af \n\U0001f4b1 '+par+' | \u23F0 '+str(minutos_lista[:-3])+' | \u231B M'+str(timeframe)+' | \u2139\ufe0f'+opcao+' \n\U0001F4B4 R$'+str(round(valor_entrada_b, 2))+' | '+direcao.upper())
            dir = False
            dir = direcao

            if dir:
                #mensagem_operacao = f' M{str(timeframe)} | {par} | {opcao} | {str(minutos_lista)} | {str(dir).upper()}'
                #Mensagem(mensagem_operacao)
                #print('----------------------------------------------------------------------------------------------')
                valor_entrada = valor_entrada_b
                opcao = 'binaria' if (opcao == 60) else opcao
                resultado, lucro, stop = entradas(par, valor_entrada, dir, config, opcao, timeframe)
                lucroTotal += lucro
                r_color = Fore.GREEN if resultado == 'win' else Fore.RED if resultado == 'loss' else Fore.RESET
                mensagem_resultado = f' \U0001F3C1 RESULTADO \U0001F3C1\n{r_color+resultado.upper()+Fore.RESET} | \U0001f4b1 {par} | {str(minutos_lista)} | M{str(timeframe)} | \U0001f4b8 R${str(lucro)}\n \U0001F4B0Lucro: R${str(round(lucroTotal, 2))}\n\a'
                Mensagem(mensagem_resultado)
                print('----------------------------------------------------------------------------------------------')
                # print(resultado)
                if resultado == 'error':
                    GravaLog(linha_log, 'ERROR')
                    break

                if (resultado == 'win' or resultado == 'doji') and stop == False:
                    GravaLog(linha_log, resultado)
                    break

                if stop:
                    mensagem_stop = '\n\U0001F6AB\U0001F6AB' if resultado == 'loss' else '\n\U0001F4B5\U0001F4B5'
                    mensagem_stop = mensagem_stop+'Stop '+resultado.upper()+' batido!'
                    Mensagem(mensagem_stop)
                    GravaLog(linha_log, resultado)
                    GravaLog('STOP', 'Stop '+resultado.upper()+' batido!')
                    start_bot = 1
                    sys.exit()

                if resultado == 'loss' and config['martingale'] == 'S':
                    valor_entrada = Martingale(float(valor_entrada))
                    for i in range(int(config['niveis']) if int(config['niveis']) > 0 else 1):

                        mensagem_martingale = f' {Fore.YELLOW}MARTINGALE NIVEL {str(i+1)} \u27a1\ufe0f [{par} | M{str(timeframe)}]. {Fore.RESET}\u231B'
                        Mensagem(mensagem_martingale)
                        resultado, lucro, stop = entradas(par, valor_entrada, dir, config, opcao, timeframe)
                        lucroTotal += lucro
                        r_color = Fore.GREEN if resultado == 'win' else Fore.RED if resultado == 'loss' else Fore.RESET
                        mensagem_resultado_martingale = (
                            ' \U0001F3C1 '+str((i+1)*('\u267b\ufe0f' if resultado == 'win' else '\U0001f6a8'))+' RESULTADO '
                            ''+str((i+1)* ('\u267b\ufe0f' if resultado == 'win' else '\U0001f6a8'))+' \U0001F3C1\n'
                            ''+r_color+resultado.upper()+Fore.RESET+str((i+1)*'\U0001F414')+' | \U0001f4b1 '+par+' | M'+str(timeframe)+''
                            ' | \U0001f4b8 R$'+str(lucro)+'\n \U0001F4B0Lucro: R$'+str(round(lucroTotal, 2))+'\n\a')
                        Mensagem(mensagem_resultado_martingale)
                        print('----------------------------------------------------------------------------------------------\n')

                        if stop:
                            mensagem_stop = '\n\U0001F6AB\U0001F6AB' if resultado == 'loss' else '\n\U0001F4B5\U0001F4B5'
                            mensagem_stop = mensagem_stop+'Stop '+resultado.upper()+' batido!'
                            Mensagem(mensagem_stop)
                            GravaLog(linha_log, resultado)
                            GravaLog('STOP', 'Stop '+resultado.upper()+' batido!')
                            start_bot = 1
                            sinais = []
                            print(start_bot)
                            sys.exit()

                        
                        if resultado == 'win' or resultado == 'doji':
                            #print('\n')
                            GravaLog(linha_log, resultado+' '+str(i+1))
                            break
                        else:
                            valor_entrada = Martingale(float(valor_entrada))

                    if resultado == 'loss':
                        GravaLog(linha_log, resultado)
                    break
                else:
                    break
        time.sleep(0.1)
####################
def hora():
    global start_bot
    while start_bot == 0:
        print(datetime.now().strftime(' %d.%m.%Y %H:%M:%S')+' -> ['+str(len(sinais))+' sinais]' , end='\r')
        time.sleep(1)
thread_hora = Thread(target=hora, args=())
thread_hora.start()
##########################
espera = 1
while True:
    if start_bot == 1 or stop_win == True or stop_loss == True:
        time.sleep(espera)
        sinais = []
        break
    for x in sinais:
        entrar = False
        try:
            timeframe_retorno = Timeframe(x.split(';')[0])
            timeframe = 0 if (timeframe_retorno == 'error') else timeframe_retorno
            par = x.split(';')[1].upper()
            minutos_lista = x.split(';')[2]
            direcao = x.split(';')[3].lower().replace('\n', '')
            espera = int(timeframe) * 61
            t = timestamp_converter()
            s = minutos_lista
            f = '%H:%M:%S'
            dif = (datetime.strptime(t, f) - datetime.strptime(s, f)).total_seconds()
            if dif > 0:
                sinais.remove(x)
                continue    
            dif = abs(dif)
            if dif == 40:
                mensagem_paridade = f' \n\u23F3Em Espera:\u23F3\n\U0001f4b1 {par} | M{str(timeframe)} | {str(minutos_lista[:-3])} | {direcao.upper()}  \U0001f440'
                print('----------------------------------------------------------------------------------------------')
                Mensagem(mensagem_paridade)
                thread = Thread(target=Operar, args=(timeframe_retorno,timeframe, par, minutos_lista, direcao))
                thread.start()
                sinais.remove(x)
        except Exception as e:
            print('\nErro encontrado: '+str(e)+'\n')
            sinais.remove(x)
    #carrega mais possiveis sinais ao vivo adicionados
    novos_sinais = carregaSinais()
    if len(novos_sinais) > 0:
        sinais = sinais + novos_sinais
        Mensagem('\n\U0001f50bTotal de '+str(len(sinais))+' sinais em buffer.\U0001F6A6\n')
        novos_sinais = []
    time.sleep(0.15)

Mensagem('\U0001F4A5 Lista de sinais finalizada!')
banca_att = banca()
Mensagem(f'\U0001F4B0 Banca: R${banca_att}')
Mensagem(f'\U0001F9FE Lucro: R${str(round(lucroTotal, 2))}')
GravaLog(' -> Lista de sinais finalizada! ', 'BANCA: ' + str(banca_att) + ' - LUCRO: '+ str(round(lucroTotal, 2)))

input()
sys.exit()