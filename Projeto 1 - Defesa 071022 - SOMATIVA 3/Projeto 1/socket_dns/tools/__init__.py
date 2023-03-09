DEFAULT_ENCODING = "utf-8"

TYPCMD_CMD_SEP = "+"
CMD_PARAMS_SEP = ":"
PARAMS_SEP = ","

TAB = "     "

TRUE = "true"
FALSE = "false"


def printHeader(prompt):
      # Imprime um cabeçalho
      print(f"\n\033[1;33m{prompt}\033[m")


def printSucess(prompt):
      # Imprime uma mensagem de sucesso
      print(f"\033[1;34m{prompt}\033[m")


def printError(prompt, erro=Exception()):
      # Imprime uma mensagem de erro
      try:
            print(f"\033[1;31m{prompt} ({erro.__class__.__name__}, {erro.args[0]})\033[m")
      except:
            print(f"\033[1;31m{prompt} (Não identificado, {None})\033[m")


def counterPerTurn():
      counter = 0
      while True:
            yield counter
            counter += 1


def createFileIfNotExits(path):
      # Cria o arquivo em path, caso não exista
      try:
            open(path, "x").close()
      except:
            pass


def saveInLogFile(path, user, domain):
      # Salva em um arquivo log o domínio requerido pelo usuária na tradução
      user = "CLIENTE " + user + ":\n"
      domain =  TAB + domain + "\n"
      with open(path, "r", encoding=DEFAULT_ENCODING) as r_file:
            lines = r_file.readlines()
            
            if user in lines:
                  index = lines.index(user) + 1
                  for i in range(len(lines) - index):
                        if ":\n" in lines[i + index]:
                              lines.insert(i + index, domain)
                              break
                        elif i + index == len(lines) - 1:
                              lines.append(domain)
            else:
                  lines.append(user)
                  lines.append(domain)
      with open(path, "w", encoding=DEFAULT_ENCODING) as w_file:
            w_file.write("".join(lines))


def dumpsCmd(typecmd, command = "", *params):
      # Monta o comando para envio baseado no comando e nos parâmetros passados
      cmd = typecmd + TYPCMD_CMD_SEP + command + CMD_PARAMS_SEP
      for i, param in enumerate(params):
            cmd += param
            if i < len(params) - 1:
                  cmd += PARAMS_SEP
      return cmd


def loadsCmd(cmd):
      # Prepara o comando para ser analisado pelo servidor/cliente
      cmd = cmd.split(CMD_PARAMS_SEP)
      params = cmd[1].split(PARAMS_SEP) if PARAMS_SEP in cmd[1] else [cmd[1]]
      cmd = cmd[0].split(TYPCMD_CMD_SEP)
      typecmd = cmd[0]
      command = cmd[1]
      return typecmd, command, params
