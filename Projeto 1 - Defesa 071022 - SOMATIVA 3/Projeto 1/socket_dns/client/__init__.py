import socket_dns.tools as tools

import socket

class client:

      BUFFER_SIZE = 4096 #4KB # Tamanho do Buffer para o recebimento de informações

      isRunning = True
      isLogged = False

      MSG_NOT_AUTH = "Não autorizado" # Mensagem por não autorização de login no servidor
      MSG_END_SEARCH = "sair" # Mensagem para encerrar a tradução de domínios por endereços IP

      def __init__(self, af, sockettype):
            tools.printHeader("Iniciando o cliente...")
            #self.myAdress = myAdress # Define o adress desse cliente -> (HOST[String], PORT[int]) (Obs.: Portas abaixo de 1023 exigem permissão de root)
            self.af = af # Define o Adress Family (IPV4, IPV6, ...)
            self.sockettype = sockettype # Define o tipo de Socket (TCP/Stream, UDP/Datagram, IP/RAW)

            try:
                  # Cria um Socket inical baseado no IPV4 (Adress Family INET) e no TCP (Stream)
                  self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

                  # Solicita um porta de transporta ao SO
                  # self.socket.bind(myAdress)
            except Exception as erro:
                  tools.printError("Erro na inicialização do cliente", erro)
                  exit()


      def connect(self, adress):
            # Tenta conectar com o servidor no endereço adress
            tools.printHeader(f"Conectando com {adress[0]} na porta {adress[1]}...")
            try:
                  self.socket.connect(adress)
            except Exception as erro:
                  tools.printError(f"Não foi possível a conexão com {adress[0]} na porta {adress[1]}", erro)
            else:
                  tools.printSucess(f"Conectado com sucesso com {adress[0]} na porta {adress[1]}")
                  self.start()

      
      def start(self):
            ### VARIÁVEIS PERSONALIZADAS AQUI ###
            
            ### ############################# ###

            try:
                  while self.isRunning:
                        typecmd = command = params = None

                        if self.isRunning and self.isLogged:
                              ### CÓDIGO PERSONALIZADO AQUI ###
                              dominio = input(f'\033[32mDigite o domínio para tradução ["{self.MSG_END_SEARCH}" encerra a comunicação]: \033[m').strip().lower()
                              if not dominio == self.MSG_END_SEARCH:
                                    self.sendCmd("get", "ipserver", dominio)
                              else:
                                    self.sendCmd("kill", )
                                    self.isRunning = False
                              ### ######################### ###

                        if self.isRunning:
                              # Inicia a comunicação com o servidor
                              typecmd, command, params = self.recvCmd()

                        # Avalia o comando recebido de acordo com o tipo
                        match typecmd:
                              case "get":
                                    returnParams = self.matchGetCmd(command, *params)
                                    if len(returnParams) > 0:
                                          self.sendCmd("snd", command, *returnParams)
                              case "snd":
                                    self.matchSndCmd(command, *params)
                              case "ack":
                                    self.matchAckCmd(command, *params)
                              case "kill":
                                    self.isRunning = False
                                    tools.printSucess(f"Conexão com servidor abortada pelo servidor")
                              case None:
                                    pass
                              case _:
                                    tools.printError("Tipo de comando inexistente no protocolo")
            except Exception as erro:
                  tools.printError("Erro no Cliente", erro)
            
            tools.printHeader("Fim do Cliente")
            self.close()


      def close(self):
            # Finaliza o cliente
            tools.printHeader("Encerrando cliente...")
            try:
                  self.socket.close()
            except Exception as erro:
                  tools.printError("Erro ao encerrar o cliente", erro)
            else:
                  tools.printSucess("Cliente encerrado com sucesso")
      
      
      def sendCmd(self, typecmd, command="", *params):
            # Envia um comando ao servidor
            tools.printHeader("Enviando comando...")
            try:
                  self.socket.send(bytes(tools.dumpsCmd(typecmd, command, *params), encoding=tools.DEFAULT_ENCODING))
            except Exception as erro:
                  tools.printError("Erro no envio de comando", erro)
            else:
                  tools.printSucess(f"Comando enviado com sucesso")

      
      def recvCmd(self):
            # Recebe um comando do servidor
            tools.printHeader("Recebendo comando...")
            cmd = bytes()
            try:
                  cmd = self.socket.recv(self.BUFFER_SIZE).decode(tools.DEFAULT_ENCODING)
            except Exception as erro:
                  tools.printError("Erro no recebimento de comando", erro)
            else:
                  tools.printSucess("Comando recebido com sucesso")
            return tools.loadsCmd(cmd)


      # TRATAMENTO DE COMANDOS:

      def matchGetCmd(self, command="", *params):
            # Executa os comandos de tipo get (havendo necessariamente retorno)
            returnParams = list()
            match command:
                  case "login":
                        tools.printHeader("Login foi requisitado pelo servidor")
                        returnParams.append(self.srv_login())
                  case _:
                        tools.printError("Comando inexistente no protocolo")
            return tuple(*returnParams)

      
      def matchSndCmd(self, command="", *params):
            # Executa os comandos de tipo snd (não havendo necessariamente retorno)
            match command:
                  case "ipserver":
                        from socket_dns.server import MSG_NOT_FOUND_DNS
                        tools.printSucess(f"IP {params[0]} recebido" if params[0] != MSG_NOT_FOUND_DNS else MSG_NOT_FOUND_DNS)
                  case _:
                        tools.printError("Comando inexistente no protocolo")
      

      def matchAckCmd(self, command="", *params):
            # Executa os comandos de tipo ack
            match command:
                  case "login":
                        if params[0] == tools.TRUE:
                              tools.printSucess("Logado com sucesso")
                              self.isLogged = True
                        else:
                              tools.printError("Erro no login (Usuário e/ou senha estão errados)")
                              tools.printSucess(self.MSG_NOT_AUTH)
                              tools.printSucess("Programa abortado com sucesso")
                              self.sendCmd("kill", )
                              self.isRunning = False
                  case _:
                        tools.printError("Comando inexistente no protocolo")

      # FUNÇÕES PARA TRATAMENTO DE COMANDOS
      # (começam com "srv_")

      def srv_login(self):
            # Imprime tela de login e retorna usuário e senha
            user = input("Usuário: ")
            password = input("Senha: ")
            return user, password
