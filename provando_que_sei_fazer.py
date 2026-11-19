import mysql.connector
import bcrypt
import random
import uuid
from decimal import Decimal


class BancoDados:
    def conectar(self):
        self.conexao = mysql.connector.connect(
            host="localhost", user="root",
            password="", database="trabalho_banco"
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
        self.cursor.close()
        self.conexao.close()


class Usuario:
    def __init__(self, id_usuario, login, perfil, senha_hash):
        self.id_usuario = id_usuario
        self.login = login
        self.perfil = perfil
        self.senha_hash = senha_hash

    def autenticar(self, senha):
        return bcrypt.checkpw(senha.encode(), self.senha_hash.encode())


class Gerente(Usuario):
    def cadastrar_cliente(self, banco, nome, cpf, telefone, email, login, senha):
        senha = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

        banco.executar(
            "INSERT INTO usuarios (login, senha_hash, perfil, ativo) VALUES (%s,%s,'CLIENTE',1)",
            (login, senha)
        )

        banco.executar(
            "INSERT INTO clientes (id_usuario,nome,cpf,telefone,email,data_cadastro) VALUES (%s,%s,%s,%s,%s,CURDATE())",
            (banco.cursor.lastrowid, nome, cpf, telefone, email)
        )
        print("Cliente cadastrado!")

    def listar_clientes(self, banco):
        if self.perfil != "GERENTE":
            raise Exception("Acesso negado!")

        for cliente in banco.consultar("SELECT id_cliente,nome,cpf,telefone,email FROM clientes"):
            print(cliente)

    def abrir_conta(self, banco, id_cliente):
        if self.perfil != "GERENTE":
            raise Exception("Acesso negado!")

        numero = str(random.randint(1000, 9999))
        banco.executar(
            "INSERT INTO contas (id_cliente,numero_conta,saldo,data_abertura,status) VALUES (%s,%s,0,CURDATE(),'ATIVA')",
            (id_cliente, numero)
        )
        print("Conta aberta! Número:", numero)

    def bloquear_conta(self, banco, id_conta):
        if self.perfil != "GERENTE":
            raise Exception("Acesso negado!")

        banco.executar(
            "UPDATE contas SET status=IF(status='ATIVA','BLOQUEADA','ATIVA') WHERE id_conta=%s",
            (id_conta,)
        )
        print("Status atualizado!")


class Cliente(Usuario):
    def __init__(self, id_usuario, login, perfil, senha_hash, id_cliente):
        super().__init__(id_usuario, login, perfil, senha_hash)
        self.id_cliente = id_cliente

    def consultar_saldo(self, conta):
        conta.exibir_saldo(self.id_cliente)

    def depositar(self, conta, valor):
        conta.movimentar(self.id_cliente, valor, "DEPOSITO")

    def sacar(self, conta, valor):
        conta.movimentar(self.id_cliente, valor, "SAQUE")

    def transferir(self, conta, destino, valor):
        conta.transferir(self.id_cliente, destino, valor)

    def consultar_extrato(self, banco, id_conta):
        return banco.consultar(
            "SELECT tipo,valor,data_movimentacao,descricao FROM movimentacoes WHERE id_conta=%s ORDER BY data_movimentacao DESC",
            (id_conta,)
        )


class ContaBancaria:
    def __init__(self, banco, id_conta):
        self.banco = banco
        self.id_conta = id_conta

    def validar_conta(self, id_cliente):
        self.banco.cursor.execute(
            "SELECT saldo,status FROM contas WHERE id_conta=%s AND id_cliente=%s",
            (self.id_conta, id_cliente)
        )
        conta = self.banco.cursor.fetchone()

        if not conta or conta[1] != "ATIVA":
            raise Exception("Conta não encontrada ou bloqueada!")

        return Decimal(str(conta[0]))

    def exibir_saldo(self, id_cliente):
        print(f"Saldo: R$ {self.validar_conta(id_cliente):.2f}")

    def movimentar(self, id_cliente, valor, tipo):
        valor = Decimal(str(valor))
        saldo = self.validar_conta(id_cliente)

        if valor <= 0 or (tipo == "SAQUE" and valor > saldo):
            raise Exception("Valor inválido ou saldo insuficiente!")

        sinal = "+" if tipo == "DEPOSITO" else "-"
        descricao = "Depósito" if tipo == "DEPOSITO" else "Saque"

        self.banco.cursor.execute(
            f"UPDATE contas SET saldo=saldo{sinal}%s WHERE id_conta=%s",
            (valor, self.id_conta)
        )
        self.banco.cursor.execute(
            "INSERT INTO movimentacoes (id_conta,tipo,valor,data_movimentacao,descricao) VALUES (%s,%s,%s,NOW(),%s)",
            (self.id_conta, tipo, valor, descricao)
        )
        self.banco.conexao.commit()
        print(descricao, "realizado!")

    def transferir(self, id_cliente, destino, valor):
        valor = Decimal(str(valor))

        if valor <= 0 or str(self.id_conta) == str(destino):
            raise Exception("Transferência inválida!")

        try:
            self.banco.conexao.start_transaction()

            self.banco.cursor.execute(
                "SELECT saldo,status FROM contas WHERE id_conta=%s AND id_cliente=%s FOR UPDATE",
                (self.id_conta, id_cliente)
            )
            origem = self.banco.cursor.fetchone()

            self.banco.cursor.execute(
                "SELECT status FROM contas WHERE id_conta=%s FOR UPDATE",
                (destino,)
            )
            fim = self.banco.cursor.fetchone()

            if not origem or origem[1] != "ATIVA":
                raise Exception("Conta de origem inválida!")

            if not fim or fim[0] != "ATIVA":
                raise Exception("Conta de destino inválida!")

            if valor > Decimal(str(origem[0])):
                raise Exception("Saldo insuficiente!")

            codigo = uuid.uuid4().hex

            for conta, sinal in [(self.id_conta, "-"), (destino, "+")]:
                self.banco.cursor.execute(
                    f"UPDATE contas SET saldo=saldo{sinal}%s WHERE id_conta=%s",
                    (valor, conta)
                )

            for conta, tipo, descricao in [
                (self.id_conta, "TRANSFERÊNCIA_ENVIADA", "Transferência enviada"),
                (destino, "TRANSFERÊNCIA_RECEBIDA", "Transferência recebida")
            ]:
                self.banco.cursor.execute(
                    "INSERT INTO movimentacoes (id_conta,tipo,valor,data_movimentacao,descricao,id_transferencia) VALUES (%s,%s,%s,NOW(),%s,%s)",
                    (conta, tipo, valor, descricao, codigo)
                )

            self.banco.conexao.commit()
            print("Transferência realizada!")

        except Exception:
            self.banco.conexao.rollback()
            raise


class SistemaBancario:
    def __init__(self):
        self.banco = BancoDados()

    def login(self):
        login = input("Login: ")
        senha = input("Senha: ")

        dados = self.banco.consultar(
        "SELECT * FROM usuarios u LEFT JOIN clientes c ON u.id_usuario=c.id_usuario WHERE u.login=%s",
        (login,)
        )

        if not dados:
            print("Usuário não encontrado!")
            return

        d = dados[0]

        if not d[4]:
            print("Usuário inativo!")
            return

        usuario = Usuario(d[0], d[1], d[3], d[2])

        if not usuario.autenticar(senha):
            print("Senha incorreta!")
        elif d[3] == "GERENTE":
            self.menu_gerente(Gerente(d[0], d[1], d[3], d[2]))
        elif d[5]:
            self.menu_cliente(Cliente(d[0], d[1], d[3], d[2], d[5]))
        else:
            print("Cliente não encontrado!")

    def menu_gerente(self, gerente):
        while True:
            print("\n===== MENU GERENTE =====")
            print("[1] Cadastrar cliente\n[2] Listar clientes")
            print("[3] Abrir conta\n[4] Bloquear conta\n[0] Sair")

            op = input("Escolha: ")

            if op == "1":
                gerente.cadastrar_cliente(
                    self.banco, input("Nome: "), input("CPF: "),
                    input("Telefone: "), input("Email: "),
                    input("Login: "), input("Senha: ")
                )
            elif op == "2":
                gerente.listar_clientes(self.banco)
            elif op == "3":
                gerente.abrir_conta(self.banco, input("ID cliente: "))
            elif op == "4":
                gerente.bloquear_conta(self.banco, input("ID conta: "))
            elif op == "0":
                break
            else:
                print("Opção inválida!")

    def menu_cliente(self, cliente):
        while True:
            print("\n===== MENU CLIENTE =====")
            print("[1] Saldo\n[2] Depositar\n[3] Sacar")
            print("[4] Transferir\n[5] Extrato\n[6] Meus dados\n[7] Sair")

            op = input("Escolha: ")

            if op == "7":
                break
            if op == "6":
                print("Login:", cliente.login, "| ID:", cliente.id_cliente)
                continue
            if op not in ["1", "2", "3", "4", "5"]:
                print("Opção inválida!")
                continue

            contas = self.banco.consultar(
                "SELECT id_conta,numero_conta FROM contas WHERE id_cliente=%s AND status='ATIVA'",
                (cliente.id_cliente,)
            )

            if not contas:
                print("Você não possui contas ativas!")
                continue

            for c in contas:
                print("Conta:", c[1], "| ID:", c[0])

            id_conta = input("ID da conta: ")
            conta = ContaBancaria(self.banco, id_conta)

            try:
                if op == "1":
                    cliente.consultar_saldo(conta)
                elif op == "2":
                    cliente.depositar(conta, input("Valor: "))
                elif op == "3":
                    cliente.sacar(conta, input("Valor: "))
                elif op == "4":
                    destino = self.banco.consultar(
                        "SELECT id_conta FROM contas WHERE numero_conta=%s",
                        (input("Conta destino: "),)
                    )
                    if destino:
                        cliente.transferir(conta, destino[0][0], input("Valor: "))
                    else:
                        print("Conta não encontrada!")
                elif op == "5":
                    for m in cliente.consultar_extrato(self.banco, id_conta):
                        print(m)

            except Exception as erro:
                print("Erro:", erro)

    def executar(self):
        self.banco.conectar()
        try:
            while True:
                print("\n===== BANCO PYTHON =====")
                op = input("[1] Entrar\n[0] Sair\nEscolha: ")

                if op == "1":
                    self.login()
                elif op == "0":
                    break
                else:
                    print("Opção inválida!")
        finally:
            self.banco.fechar()


SistemaBancario().executar()