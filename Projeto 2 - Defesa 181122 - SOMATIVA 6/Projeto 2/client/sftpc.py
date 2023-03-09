import os
import socket
import sys
import time

from pathlib import Path

SERVERHOST = '127.0.0.1'             # IP do servidor
CLIENTHOST = '127.0.0.1'             # IP do cliente
CMDPORT = 9999                       # Porta de comandos do servidor
FILEPORT = 9998                      # Porta de envio de dados do cliente

PYDIR = os.path.dirname(os.path.realpath(__file__))

# -------------------------------------------------
# FUNÇÕES SECUNDÁRIAS

# Faz o upload de um arquivo local
def uploadFile(path, conn):
      try:
            # file = open(path, 'rb')
            # conn.send(file.read())

            file = open(path, 'r')

            line = file.readline().encode('utf-8')
            while line:
                  conn.send(line)
                  line = file.readline().encode('utf-8')

            print(f"\nEnviando dados... ({os.stat(path).st_size}B)")
            file.close()
      except:
            print('\nErro de envio do arquivo.')


# Faz o download de um arquivo remoto
def downloadFile(path, conn):
      # Abre o arquivo em modo escrita
      file = open(path, 'wb')

      print("")
      while True:
            # Recebe os dados da conexão em blocos de 1000 bytes
            data = conn.recv(1000)
            print(f"Recebendo dados... ({len(data)}B)")

            if len(data) == 0 or data is None:
                  break
            else:
                  # Escreve os dados no arquivo
                  file.write(data)

      # Quando o servidor encerrar a conexão, fecha o arquivo
      file.close()


# Seleciona um diretório local pelo usuário
def selectDiretorioLocal(createDirIfNotExists=False):
      # Lista o diretório atual e seu conteúdo
      print('\nDiretório atual:', os.getcwd())
      print('\nConteúdo do diretório:')
      for d in [d for d in os.listdir() if not '.' in d]:
            print('->', d)

      dir = input('\nSelecione um diretório local ou <ENTER> para manter o atual: ')
      if len(dir) > 0:
            try:
                  # Cria o diretório se não existir
                  if not dir in os.listdir():
                        if createDirIfNotExists:
                              os.makedirs(dir)
                        else:
                              dir = "."
                              print('\nDiretório anterior mantido.')
            except:
                  dir = "."
                  print('\nDiretório anterior mantido.')

            getcwd = os.getcwd() + ("\\" if dir != "." else "") + (dir if dir != "." else "")
            print(f'\nDiretório selecionado: {getcwd}')
      else:
            dir = "."
            print('\nDiretório anterior mantido.')
      
      return dir


# Seleciona um arquivo local pelo usuário
def selectArquivoLocal(dir):
      while True:
            print('\nConteúdo do diretório:')
            for f in [f for f in os.listdir(dir) if '.' in f]:
                  print('->', f)
            
            file = input('\nSelecione um arquivo local: ')

            if not file:
                  continue

            if file in os.listdir(dir):
                  print('\nArquivo local encontrado.')
                  break
            else:
                  print('\nArquivo local não foi encontrado.')
      
      return file


# Seleciona um diretório remoto pelo usuário
def selectDiretorioRemoto(cmdSocket, createDirIfNotExists=False):
      # Lista o diretório atual e seu conteúdo
      cmdSocket.send(bytes('os.getcwd()\n', 'utf-8'))
      time.sleep(2) # Espera para receber a resposta completa sem ter que criar um while
      getcwd = cmdSocket.recv(2048).decode()
      print('\nDiretório atual:', getcwd[:-2])

      cmdSocket.send(bytes('os.listdir()\n', 'utf-8'))
      time.sleep(2) # Espera para receber a resposta completa sem ter que criar um while
      listdir = [d for d in eval(cmdSocket.recv(2048).decode()) if not '.' in d]
      print('\nConteúdo do diretório:')
      for d in listdir:
            print('->', d)

      dir = input('\nSelecione um diretório remoto ou <ENTER> para manter o atual: ')
      if len(dir) > 0:
            try:
                  # Cria o diretório se não existir
                  if not dir in listdir:
                        if createDirIfNotExists:
                              cmdSocket.send(bytes(f'os.makedirs({dir})\n','utf-8'))
                              time.sleep(2)
                              cmdSocket.recv(2048).decode()
                        else:
                              dir = "."
                              print('\nDiretório anterior mantido.')
            except:
                  dir = "."
                  print('\nDiretório anterior mantido.')

            getcwd = getcwd[:-2] + ("\\" if dir != "." else "") + (dir if dir != "." else "")
            print('\nDiretório selecionado:', getcwd)
      else:
            dir = "."
            print('\nDiretório anterior mantido.')
      
      return dir


# Seleciona um arquivo remoto pelo usuário
def selectArquivoRemoto(cmdSocket, dir):
      cmdSocket.send(bytes(f'os.listdir({dir})\n', 'utf-8'))
      time.sleep(2) # Espera para receber a resposta completa sem ter que criar um while
      listdir = [f for f in eval(cmdSocket.recv(2048).decode()) if '.' in f]
      while True:
            print('\nConteúdo do diretório:')
            for f in listdir:
                  print('->', f)

            file = input('\nSelecione um arquivo remoto: ')

            if not file:
                  continue

            if file in listdir:
                  print('\nArquivo remoto encontrado.')
                  break
            else:
                  print('\nArquivo remoto não foi encontrado.')

      return file

# -------------------------------------------------


# -------------------------------------------------
# FUNÇÕES PRINCIPAIS

# Faz o upload para o servidor de um arquivo local
def uploadFileToServer():
      print('\n\n\033[33;1;4mUPLOAD PARA O SERVER\033[m')

      # Cria o socket de comandos
      cmdSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      try:
            cmdSocket.connect((SERVERHOST, CMDPORT))
      except:
            print('\nErro de conexão do socket de comandos.')
            return
            
      # Seleciona o diretório padrão como o default
      os.chdir(PYDIR)

      # Seleciona o diretório local
      print('\n\033[34mSelecione o diretório local do arquivo a ser enviado:\033[m')
      dir = selectDiretorioLocal()

      # Seleciona o arquivo local
      print('\n\033[34mSelecione o arquivo local a ser enviado:\033[m')
      arquivo = selectArquivoLocal(dir)

      # Seleciona o diretório remoto
      print('\n\033[34mSelecione o diretório remoto para armazenar o arquivo:\033[m')
      serverDir = selectDiretorioRemoto(cmdSocket, createDirIfNotExists=True)

      # Cria o socket de envio de dados
      fileSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      try:
            fileSocket.bind((CLIENTHOST, FILEPORT))
            fileSocket.listen(1)
      except:
            print('\nErro de conexão do socket de envio de dados.')
            return

      # Envia ordem de upload ao servidor
      cmdSocket.send(bytes(f'upload({os.path.join(serverDir, arquivo)})\n', 'utf-8'))

      # Aguarda a conexão para criar o canal de dados
      conn, addr = fileSocket.accept()

      # Chama a função que transferência de arquivo pelo canal de dados
      uploadFile(Path(dir + '/' + arquivo), conn)

      conn.close()

      print('\n\033[34mUpload concluído com sucesso.\033[m')

      cmdSocket.close()
      fileSocket.close()

      input('\nDigite <ENTER> para encerrar.')


# Faz o download para o local de um arquivo do servidor
def downloadFileFromServer():
      print('\n\n\033[33;1;4mDOWNLOAD DO SERVER\033[m')

      # Cria o socket principal do cliente com o servidor
      cmdSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      try:
            cmdSocket.connect((SERVERHOST, CMDPORT))
      except:
            print('\nErro de conexão.')
            return

      # Seleciona o diretório padrão como o default
      os.chdir(PYDIR)

      # Seleciona o diretório remoto
      print('\n\033[34mSelecione o diretório remoto do arquivo a ser baixado:\033[m')
      dir = selectDiretorioRemoto(cmdSocket)

      # Seleciona o arquivo remoto
      print('\n\033[34mSelecione o arquivo remoto a ser baixado:\033[m')
      arquivo = selectArquivoRemoto(cmdSocket, dir)

      # Seleciona o diretório local
      print('\n\033[34mSelecione a pasta local para salvar o arquivo:\033[m')
      clientDir = selectDiretorioLocal(createDirIfNotExists=True)

      # Cria o socket de envio de dados
      fileSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      try:
            fileSocket.bind((CLIENTHOST, FILEPORT))
            fileSocket.listen(1)
      except:
            print('\nErro de conexão do socket de envio de dados.')
            return

      # Envia ordem de download ao servidor
      cmdSocket.send(bytes(f'download({os.path.join(dir, arquivo)})\n', 'utf-8'))

      # Aguarda a conexão para criar o canal de dados
      conn, addr = fileSocket.accept()

      # Chama a função que transferência de arquivo pelo canal de dados
      downloadFile(Path(clientDir + '/' + arquivo), conn)

      conn.close()

      print('\n\033[34mDownload concluído com sucesso.\033[m')

      cmdSocket.close()

      input('\nDigite <ENTER> para encerrar.')

# -------------------------------------------------


# -------------------------------------------------
# MAIN

def main():
      print('\nSimple File Transfer Protocol Client')

      # Menu para o usuário selecionar a opção desejada
      while True:
            print('\nMenu:\n1 - Upload de arquivo\n2 - Download de arquivo\n0 - Finalizar programa')
            try:
                  opcao = int(input('> '))
            except:
                  print('\nDigite um valor inteiro.')
            else:
                  match(opcao):
                        case 0:
                              print('\nPrograma encerrado.')
                              sys.exit()
                        case 1:
                              print('\nIniciando upload de arquivo para o servidor...')
                              uploadFileToServer()
                        case 2:
                              print('\nIniciando download de arquivo para o servidor...')
                              downloadFileFromServer()
                        case _:
                              print('\nOpção inválida.')


if __name__ == "__main__":
      main()

# -------------------------------------------------
