import socket_dns.tools as tools

import socket
import threading

MSG_NOT_FOUND_DNS = "Domínio não encontrado na base de dados." # Mensagem para caso não seja encontrado o domínio no banco de dados

class server:

      n = 10 # Quantidade máxima de conexões pendentes autorizadas ao OS
      BUFFER_SIZE = 4096 #4KB # Tamanho do Buffer para o recebimento de informações

      LOGIN_FILE = "data/login_data.json" # Nome e localização do arquivo contendo os pares de usuário e de senha
      DNS_FILE = "data/dns_data.json" # Nome e localização do arquivo contendo as associações entre domínios e endereços IPv4
      LOG_FILE = "log.txt" # Arquivo de log para as requisições dos clientes

      lock = threading.Lock() # Lock para as threads

      activeClients = list() # Todos os clientes ativos (conexões e threads ativas) no servidor em pares
      # Guarda uma lista de dicts com "thread" (com a thread do cliente), "conn" (com a conexão do cliente) e "adrss" (com o endereço do cliente)

      def __init__(self, myAdress, af, sockettype):
            tools.printHeader("Iniciando o servidor...")
            self.myAdress = myAdress # Define o adress desse servidor -> (HOST[String], PORT[int]) (Obs.: Portas abaixo de 1023 exigem permissão de root)
            self.af = af # Define o Adress Family (IPV4, IPV6, ...)
            self.sockettype = sockettype # Define o tipo de Socket (TCP/Stream, UDP/Datagram, IP/RAW)

            tools.createFileIfNotExits(self.LOGIN_FILE) # Cria o arquivo de login, caso não exista
            tools.createFileIfNotExits(self.DNS_FILE) # Cria o arquivo de DNS, caso não exista
            tools.createFileIfNotExits(self.LOG_FILE) # Cria o arquivo de Log, caso não exista

            with open(self.LOG_FILE, "r", encoding=tools.DEFAULT_ENCODING) as rfile:
                  log_file = rfile.readlines()
                  if not "RESOLUÇÕES:\n" in log_file:
                        log_file.insert(0, "RESOLUÇÕES:\n")
            with open(self.LOG_FILE, "w", encoding=tools.DEFAULT_ENCODING) as wfile:
                  wfile.write("".join(log_file))

            try:
                  # Cria um Socket inical baseado no IPV4 (Adress Family INET) e no TCP (Stream)
                  self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

                  # Solicita um porta de transporta ao SO
                  self.socket.bind(myAdress)

                  # Autoriza o SO a receber até n conexões pendentes
                  self.socket.listen(self.n)
            
            except Exception as erro:
                  tools.printError(f"Erro na inicialização do servidor", erro)
                  exit()


      def start(self):
            # Inicia uma thread de cliente que aguarda conexão
            self.newClientThread()


      def awaitRunning(self):
            # Aguarda Threads terminarem de rodar
            for client in self.activeClients:
                  client["thread"].join()


      def newClientThread(self):
            # Cria uma thread para um cliente
            self.lock.acquire()
            thread = threading.Thread(target=self.clientThread, args=(len(self.activeClients), ))
            self.activeClients.append({"thread": thread})
            self.lock.release()

            thread.start()


      def clientThread(self, index):
            # Função Thread para o cliente
            self.awaitConn(index)
            self.newClientThread()

            isRunning = True
            isLogged = False

            try:
                  while isRunning and not isLogged:
                        self.sendCmd(index, "get", "login", "") # Requere login para acesso
                        typecmd, command, params = self.recvCmd(index)

                        if typecmd == "kill":
                              isRunning = False
                              tools.printSucess(f"Thread {index + 1} abortada pelo cliente")
                              break

                        if typecmd != "snd" or command != "login":
                              continue
                        else:
                              if self.clt_auth(params[0], params[1]):
                                    isLogged = True
                                    user = params[0]
                                    self.returnAckToClient(index, True) # Informa sobre o sucesso do login
                              else:
                                    self.returnAckToClient(index, False) # Informa sobre o fracasso do login
            
                  while isRunning:
                        # Fica em modo de espera por comandos do cliente
                        typecmd, command, params = self.recvCmd(index)

                        # Avalia o comando recebido de acordo com o tipo
                        match typecmd:
                              case "get":
                                    returnParams = self.matchGetCmd(user, index, command, *params)
                                    if len(returnParams) > 0:
                                          self.sendCmd(index, "snd", command, *returnParams)
                              case "snd":
                                    self.matchSndCmd(user, index, command, *params)
                              case "kill":
                                    isRunning = False
                                    tools.printSucess(f"Thread {index + 1} abortada pelo cliente")
                              case _:
                                    tools.printError("Tipo de comando inexistente no protocolo")
            except Exception as erro:
                  tools.printError(f"Erro na Thread {index + 1}", erro)

            tools.printHeader(f"Fim da Thread {index + 1}")
            self.closeClient(index)


      def awaitConn(self, index):
            # Espera por conexão na porta e guarda ela
            tools.printHeader(f"Thread {index + 1} aguardando conexão em {self.myAdress[0]}:{self.myAdress[1]}...")
            try:
                  conn, adrss = self.socket.accept()
            except Exception as erro:
                  tools.printError("Erro de conexão", erro)
            else:
                  tools.printSucess(f"Conectado com sucesso com cliente {adrss[0]}:{adrss[1]}")
                  self.activeClients[index]["conn"] = conn
                  self.activeClients[index]["adrss"] = adrss


      def closeClient(self, index):
            # Finaliza uma conexão
            tools.printHeader(f"Encerrando conexão com cliente {index + 1}...")
            try:
                  self.activeClients[index]["conn"].close()
            except Exception as erro:
                  tools.printError("Erro ao encerrar conexão", erro)
            else:
                  tools.printSucess("Encerrado com sucesso")


      def close(self):
            # Finaliza o servidor
            tools.printHeader("Encerrando servidor...")
            try:
                  for i in range(len(self.activeClients)):
                        self.closeClient(i)
                  self.socket.close()
            except Exception as erro:
                  tools.printError("Erro ao encerrar o servidor", erro)
            else:
                  tools.printSucess("Servidor encerrado com sucesso")


      def sendCmd(self, index, typecmd, command="", *params):
            # Envia um comando ao cliente
            tools.printHeader(f"Enviando comando ao cliente {index + 1}...")
            try:
                  self.activeClients[index]["conn"].send(bytes(tools.dumpsCmd(typecmd, command, *params), tools.DEFAULT_ENCODING))
            except Exception as erro:
                  tools.printError("Erro no envio de comando", erro)
            else:
                  tools.printSucess(f"Comando enviado com sucesso")

      
      def recvCmd(self, index):
            # Recebe um comando do cliente
            tools.printHeader(f"Recebendo comando do cliente {index + 1}...")
            cmd = bytes()
            try:
                  cmd = self.activeClients[index]["conn"].recv(self.BUFFER_SIZE).decode(tools.DEFAULT_ENCODING)
            except Exception as erro:
                  tools.printError("Erro no recebimento de comando", erro)
            else:
                  tools.printSucess("Comando recebido com sucesso")
            return tools.loadsCmd(cmd)
      

      def returnAckToClient(self, index, ack_bool):
            # Retorna um comando do tipo ack para o cliente
            self.sendCmd(index, "ack", "login", tools.TRUE if ack_bool else tools.FALSE)


      # TRATAMENTO DE COMANDOS:

      def matchGetCmd(self, user, index, command="", *params):
            # Executa os comandos de tipo get (havendo necessariamente retorno)
            returnParams = list()
            match command:
                  case "ipserver":
                        returnParams.append(self.clt_matchIpServer(user, params[0]))
                  case _:
                        tools.printError("Comando inexistente no protocolo")
            return returnParams

      
      def matchSndCmd(self, user, index, command="", *params):
            # Executa os comandos de tipo snd (não havendo necessariamente retorno)
            match command:
                  case _:
                        tools.printError("Comando inexistente no protocolo")

      # FUNÇÕES PARA TRATAMENTO DE COMANDOS
      # (começam com "clt_")

      def clt_auth(self, user, password):
            # Valida a existência do par usuário com senha
            from json import loads
            with open(self.LOGIN_FILE, "r") as file:
                  login_file = loads(file.read())

            login = {"user": user, "password": password}

            if login in login_file:
                  return True
            else:
                  return False


      def clt_matchIpServer(self, user, domain):
            # Retorna IPv4 do site com domínio passado se houver (e guarda no log)
            from json import loads

            self.lock.acquire()
            tools.saveInLogFile(self.LOG_FILE, user, domain)
            self.lock.release()

            with open(self.DNS_FILE, "r") as file:
                  dns_file = loads(file.read())
                  
            if domain in dns_file.keys():
                  return dns_file[domain]
            else:
                  return MSG_NOT_FOUND_DNS
