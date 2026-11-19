import mysql.connector

class BancoDados:
    def __init__(self):
        self.conexao = None
        self.cursor = None

    def conectar(self):
        self.conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="trabalho_banco"
        )
        self.cursor = self.conexao.cursor()
        print("Banco conectado!")

    def executar(self, sql, valores=None):
        self.cursor.execute(sql, valores or ())
        self.conexao.commit()

    def consultar(self, sql, valores=None):
        self.cursor.execute(sql, valores or ())
        return self.cursor.fetchall()

    def fechar(self):
        if self.cursor:
            self.cursor.close()

        if self.conexao:
            self.conexao.close()


class Usuario:
    def __init__(self, id_usuario, login, perfil, senha_hash):
        self.id_usuario = id_usuario
        self.login = login
        self.perfil = perfil
        self.senha_hash = senha_hash

    def autenticar(self, senha):
        import bcrypt

        return bcrypt.checkpw(
            senha.encode(),
            self.senha_hash.encode()
        )


class Gerente(Usuario):

    def cadastrar_cliente(self, banco, nome, cpf, telefone, email, login, senha):
        import bcrypt

        senha_hash = bcrypt.hashpw(
            senha.encode(),
            bcrypt.gensalt()
        ).decode()

        banco.executar(
            "INSERT INTO usuarios (login, senha_hash, perfil, ativo) VALUES (%s, %s, %s, %s)",
            (login, senha_hash, "CLIENTE", 1)
        )

        id_usuario = banco.cursor.lastrowid

        banco.executar(
            "INSERT INTO clientes (id_usuario, nome, cpf, telefone, email, data_cadastro) VALUES (%s, %s, %s, %s, %s, CURDATE())",
            (id_usuario, nome, cpf, telefone, email)
        )

        print("Cliente cadastrado com sucesso!")

    def listar_clientes(self, banco):
        if self.perfil != "GERENTE":
            raise Exception("Acesso negado!")

        clientes = banco.consultar(
            "SELECT id_cliente, nome, cpf, telefone, email FROM clientes"
        )

        for cliente in clientes:
            print(cliente)

    def abrir_conta(self, banco, id_cliente):
        import random

        if self.perfil != "GERENTE":
            raise Exception("Acesso negado!")

        numero = str(random.randint(1000, 9999))

        banco.executar(
            "INSERT INTO contas (id_cliente, numero_conta, saldo, data_abertura, status) VALUES (%s, %s, %s, CURDATE(), %s)",
            (id_cliente, numero, 0, "ATIVA")
        )

        print("Conta aberta com sucesso!")
        print("Número da conta:", numero)

    def bloquear_conta(self, banco, id_conta):
        if self.perfil != "GERENTE":
            raise Exception("Acesso negado!")

        banco.executar(
            "UPDATE contas SET status = IF(status = 'ATIVA', 'BLOQUEADA', 'ATIVA') WHERE id_conta = %s",
            (id_conta,)
        )

        print("Status da conta atualizado!")



class Cliente(Usuario):
    def __init__(self, id_usuario, login, perfil, senha_hash, id_cliente):
        super().__init__(id_usuario, login, perfil, senha_hash)
        self.id_cliente = id_cliente

    def consultar_saldo(self, conta):
        return conta.exibir_saldo(self.id_cliente)

    def depositar(self, conta, valor):
        return conta.depositar(self.id_cliente, valor)

    def sacar(self, conta, valor):
        return conta.sacar(self.id_cliente, valor)

    def transferir(self, conta, destino, valor):
        return conta.transferir(self.id_cliente, destino, valor)

    def consultar_extrato(self, banco, id_conta):
        return banco.consultar(
            "SELECT tipo, valor, data_movimentacao, descricao FROM movimentacoes WHERE id_conta = %s ORDER BY data_movimentacao DESC",
            (id_conta,)
        )


from decimal import Decimal

class ContaBancaria:
    def __init__(self, banco, id_conta):
        self.banco = banco
        self.id_conta = id_conta

    def validar_conta(self, id_cliente):
        self.banco.cursor.execute(
            "SELECT saldo, status FROM contas WHERE id_conta = %s AND id_cliente = %s",
            (self.id_conta, id_cliente)
        )
        conta = self.banco.cursor.fetchone()

        if not conta:
            raise Exception("Conta não encontrada!")

        if conta[1] != "ATIVA":
            raise Exception("Conta bloqueada!")

        return Decimal(str(conta[0]))

    def exibir_saldo(self, id_cliente):
        saldo = self.validar_conta(id_cliente)
        print(f"Saldo: R$ {saldo:.2f}")
        return saldo

    def depositar(self, id_cliente, valor):
        valor = Decimal(str(valor))

        if valor <= 0:
            raise Exception("Valor inválido!")

        self.validar_conta(id_cliente)

        self.banco.cursor.execute(
            "UPDATE contas SET saldo = saldo + %s WHERE id_conta = %s AND id_cliente = %s",
            (valor, self.id_conta, id_cliente)
        )

        self.banco.cursor.execute(
            "INSERT INTO movimentacoes (id_conta, tipo, valor, data_movimentacao, descricao) VALUES (%s, %s, %s, NOW(), %s)",
            (self.id_conta, "DEPOSITO", valor, "Depósito")
        )

        self.banco.conexao.commit()
        print("Depósito realizado!")

    def sacar(self, id_cliente, valor):
        valor = Decimal(str(valor))

        if valor <= 0:
            raise Exception("Valor inválido!")

        saldo = self.validar_conta(id_cliente)

        if valor > saldo:
            raise Exception("Saldo insuficiente!")

        self.banco.cursor.execute(
            "UPDATE contas SET saldo = saldo - %s WHERE id_conta = %s AND id_cliente = %s",
            (valor, self.id_conta, id_cliente)
        )

        self.banco.cursor.execute(
            "INSERT INTO movimentacoes (id_conta, tipo, valor, data_movimentacao, descricao) VALUES (%s, %s, %s, NOW(), %s)",
            (self.id_conta, "SAQUE", valor, "Saque")
        )

        self.banco.conexao.commit()
        print("Saque realizado!")


    def transferir(self, id_cliente, destino, valor):
        import uuid

        valor = Decimal(str(valor))
        id_transferencia = uuid.uuid4().hex

        if valor <= 0:
            raise Exception("Valor inválido!")

        if self.id_conta == destino:
            raise Exception("Não é possível transferir para a mesma conta!")

        try:
            self.banco.conexao.start_transaction()

            self.banco.cursor.execute(
                "SELECT saldo, status FROM contas WHERE id_conta = %s AND id_cliente = %s FOR UPDATE",
                (self.id_conta, id_cliente)
            )
            origem = self.banco.cursor.fetchone()

            if not origem or origem[1] != "ATIVA":
                raise Exception("Conta de origem inválida ou bloqueada!")

            self.banco.cursor.execute(
                "SELECT status FROM contas WHERE id_conta = %s FOR UPDATE",
                (destino,)
            )
            conta_destino = self.banco.cursor.fetchone()

            if not conta_destino or conta_destino[0] != "ATIVA":
                raise Exception("Conta de destino inválida ou bloqueada!")

            if valor > Decimal(str(origem[0])):
                raise Exception("Saldo insuficiente!")

            self.banco.cursor.execute(
                "UPDATE contas SET saldo = saldo - %s WHERE id_conta = %s",
                (valor, self.id_conta)
            )

            self.banco.cursor.execute(
                "UPDATE contas SET saldo = saldo + %s WHERE id_conta = %s",
                (valor, destino)
            )

            self.banco.cursor.execute(
                "INSERT INTO movimentacoes (id_conta, tipo, valor, data_movimentacao, descricao, id_transferencia) VALUES (%s, %s, %s, NOW(), %s, %s)",
                (self.id_conta, "TRANSFERÊNCIA_ENVIADA", valor, "Transferência enviada", id_transferencia)
            )

            self.banco.cursor.execute(
                "INSERT INTO movimentacoes (id_conta, tipo, valor, data_movimentacao, descricao, id_transferencia) VALUES (%s, %s, %s, NOW(), %s, %s)",
                (destino, "TRANSFERÊNCIA_RECEBIDA", valor, "Transferência recebida", id_transferencia)
            )

            self.banco.conexao.commit()
            print("Transferência realizada com sucesso!")

        except Exception as erro:
            self.banco.conexao.rollback()
            print("Erro:", erro)


class SistemaBancario:
    def __init__(self):
        self.banco = BancoDados()

    def login(self):
        login = input("Login: ")
        senha = input("Senha: ")

        usuario = self.banco.consultar(
            "SELECT u.id_usuario, u.login, u.senha_hash, u.perfil, u.ativo, c.id_cliente FROM usuarios u LEFT JOIN clientes c ON u.id_usuario = c.id_usuario WHERE u.login = %s",
            (login,)
        )

        if not usuario:
            print("Usuário não encontrado!")
            return

        dados = usuario[0]

        if not dados[4]:
            print("Usuário inativo!")
            return

        import bcrypt

        if not bcrypt.checkpw(senha.encode(), dados[2].encode()):
            print("Senha incorreta!")
            return

        if dados[3] == "GERENTE":
            usuario = Gerente(dados[0], dados[1], dados[3], dados[2])
            self.menu_gerente(usuario)

        else:
            if dados[5] is None:
                print("Cliente não encontrado!")
                return

            usuario = Cliente(
                dados[0], dados[1], dados[3], dados[2], dados[5]
            )
            self.menu_cliente(usuario)

    def menu_gerente(self, gerente):
        while True:
            print("\n===== MENU GERENTE =====")
            print("[1] Cadastrar cliente")
            print("[2] Listar clientes")
            print("[3] Abrir conta")
            print("[4] Bloquear / Desbloquear conta")
            print("[0] Sair")

            opcao = input("Escolha: ")

            if opcao == "1":
                gerente.cadastrar_cliente(
                    self.banco,
                    input("Nome: "),
                    input("CPF: "),
                    input("Telefone: "),
                    input("Email: "),
                    input("Login: "),
                    input("Senha: ")
                )

            elif opcao == "2":
                gerente.listar_clientes(self.banco)

            elif opcao == "3":
                gerente.abrir_conta(
                    self.banco,
                    input("ID do cliente: ")
                )

            elif opcao == "4":
                gerente.bloquear_conta(
                    self.banco,
                    input("ID da conta: ")
                )

            elif opcao == "0":
                break

            else:
                print("Opção inválida!")

    def menu_cliente(self, cliente):
        while True:
            print("\n===== MENU CLIENTE =====")
            print("[1] Consultar saldo")
            print("[2] Depositar")
            print("[3] Sacar")
            print("[4] Transferir")
            print("[5] Consultar extrato")
            print("[6] Meus dados")
            print("[7] Sair")

            opcao = input("Escolha: ")

            if opcao == "7":
                break

            if opcao == "6":
                print("Login:", cliente.login)
                print("ID:", cliente.id_cliente)
                continue

            contas = self.banco.consultar(
                "SELECT id_conta, numero_conta FROM contas WHERE id_cliente = %s AND status = 'ATIVA'",
                (cliente.id_cliente,)
            )

            if not contas:
                print("Você não possui contas ativas!")
                continue

            for conta in contas:
                print("Conta:", conta[1], "| ID:", conta[0])

            id_conta = input("Digite o ID da conta: ")
            conta = ContaBancaria(self.banco, id_conta)

            try:
                if opcao == "1":
                    cliente.consultar_saldo(conta)

                elif opcao == "2":
                    cliente.depositar(
                        conta, input("Valor do depósito: ")
                    )

                elif opcao == "3":
                    cliente.sacar(
                        conta, input("Valor do saque: ")
                    )

                elif opcao == "4":
                    destino = input("Número da conta de destino: ")

                    resultado = self.banco.consultar(
                        "SELECT id_conta FROM contas WHERE numero_conta = %s",
                        (destino,)
                    )

                    if resultado:
                        cliente.transferir(
                            conta, resultado[0][0],
                            input("Valor da transferência: ")
                        )
                    else:
                        print("Conta de destino não encontrada!")

                elif opcao == "5":
                    extrato = cliente.consultar_extrato(
                        self.banco, id_conta
                    )

                    for movimento in extrato:
                        print(movimento)

                else:
                    print("Opção inválida!")

            except Exception as erro:
                print("Erro:", erro)

    def executar(self):
        self.banco.conectar()

        try:
            while True:
                print("\n===== BANCO PYTHON =====")
                print("[1] Entrar")
                print("[0] Sair")

                opcao = input("Escolha: ")

                if opcao == "1":
                    self.login()

                elif opcao == "0":
                    break

                else:
                    print("Opção inválida!")

        finally:
            self.banco.fechar()
