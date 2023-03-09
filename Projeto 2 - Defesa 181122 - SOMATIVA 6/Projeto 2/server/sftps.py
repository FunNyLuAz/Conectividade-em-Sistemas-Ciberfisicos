import socket
import threading
import os
import sys
from pathlib import Path

#---------------------------------------------------

def ReadLine(conn):
    line = ''
    while True:
        try:
            byte = conn.recv(1)
        except:
            print('O cliente encerrou')
            return 0
        
        if not byte:
            return 0
        byte = byte.decode()
        if byte == '\r':
            continue
        if byte == '\n':
            break
        line += byte
    return line

#------------------------------------------------
def Upload(conn, ip, file):
    try:
        f = open(file,'w+')
    except:
        print('erro abertura arquivo')
    try:     
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip,9998))

        while True:
            data = s.recv(1024)
            #print(data.decode('utf-8'))
            f.write(data.decode('utf-8'))
            
            if not data:
                break
            
        f.close()
        s.close()
        conn.send(bytes('TRANSMISSAO ENCERRADA\n','utf-8'))
        
    except:
        f.close()
        conn.send(bytes('A PORTA DE DADOS NÃO ESTA ABERTA\n','utf-8'))

#-----------------------------------------------

def Download(conn, ip, file):
    try:
        f = open(Path(file),'rb')
    except:
        print('erro abertura arquivo')
    try:     
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip,9998))
        
        s.send(f.read())
            
        f.close()
        s.close()
        
        conn.send(bytes('TRANSMISSAO ENCERRADA\n','utf-8'))
        
    except:
        print('ERRO DE DOWNLOAD')
        f.close()
        conn.send(bytes('A PORTA DE DADOS NÃO ESTA ABERTA\n','utf-8'))

#------------------------------------------------
def TrataCliente(conn, addr):

    while True:
        conn.send(bytes('\r\n','utf-8'))
        data = ReadLine(conn)
        print('{} enviou {}'.format(addr,data))
        if data == 0:
            break
        
        try:
            if data == 'os.getcwd()':
                res=os.getcwd()
                conn.send(bytes(res,'utf-8'))
                
            elif data.startswith('os.listdir'):
                file = data.split('(')[1].split(')')[0]
                if file == '':
                    file = '.'
                res=os.listdir(file)
                conn.send(bytes(str(res),'utf-8'))
                
            elif data.startswith('os.makedirs'):
                file = data.split('(')[1].split(')')[0]
                print(file)
                if file != '':
                    os.makedirs(file)
                    conn.send(bytes('OK','utf-8'))
                else:
                    conn.send(bytes('NOK','utf-8'))
                
            elif data.startswith('upload'):
                try:
                    file = data.split('(')[1].split(')')[0]
                    Upload(conn, addr[0], file)
                except:
                    conn.send(bytes('COMANDO INVALIDO','utf-8'))
            elif data.startswith('download'):
                try:
                    file = data.split('(')[1].split(')')[0]
                    Download(conn, addr[0], file)
                except:
                    conn.send(bytes('COMANDO INVALIDO','utf-8'))
            else:
                print('teste:',data,'teste',len(data))
                conn.send(bytes('COMANDO DESCONHECIDO','utf-8'))
    
        except:
            conn.send(bytes('ERRO DESCONHECIDO\n','utf-8'))
        
 
    print('{} encerrou'.format(addr))

#---------------------------------------------------------
# PROGRAMA PRINCIPAL
#---------------------------------------------------------

print('Simple File Transfer Protocol Server\n')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind(('', 9999))
except:
   print('# erro de bind')
   sys.exit()

s.listen(5)

print('aguardando conexões na porta ', 9999)
print('Canal de controle:              cliente  ----> [9999] servidor')
print('Canal de dados (call back):     servidor ----> [9998] cliente')


while True:
    conn, addr = s.accept()
    print('recebi uma conexao do cliente ', addr)

    t = threading.Thread( target=TrataCliente, args=(conn,addr,))
    t.start()
