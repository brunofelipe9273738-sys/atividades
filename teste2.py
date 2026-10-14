import mysql.connector

conexao = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "",
    database = "nicolas"
)

print("voce se conectou ao banco!")

cursor = conexao.cursor()

def cadastrar(tabela, colunas, valores):
    campos = ', '.join(colunas)
    parametro = ', '.join(['%s'] * len(valores))

    sql = f"INSERT INTO {tabela} ({campos}) VALUES({parametro})"

    cursor.execute(sql, valores)
    conexao.commit()

def listar(tabela):
    sql = f"SELECT * FROM {tabela}"

    cursor.execute(sql)
    return cursor.fetchall()

def atualizar(tabela, coluna, valor, id_registrado):
    sql = f"UPDATE {tabela} SET {coluna} = %s WHERE id = %s"

    cursor.execute(sql, (valor, id_registrado))
    conexao.commit()

def excluir(tabela, id_registrado):
    sql = f"DELETE FROM {tabela} WHERE id = %s"

    cursor.execute(sql, (id_registrado,))
    conexao.commit()


while True:
    print("\n===Cadastro do Pet Shop do Nicolas===\n")
    print("\n1. Cadastrar: ")
    print("\n2. Logar: ")
    print("\n3. Listar: ")
    print("\n4. Apagar: ")
    print("\n5. Atualizar: ")
    print("\n6. Sair: ")

    opcao = input("\nEscolha uma opção: ")

    if opcao == "1":
        nome_usuario = input("Digite o nome de usuario: ")
        senha = input("Digite uma senha: ")
        email = input("Digite um email: ")

        cadastrar(
            "usuario",
            ["nome", "senha", "email"],
            [nome_usuario, senha , email]
        )

        print("Usuario cadastrado!")

    elif opcao == "2":
        senha = input("\nDigite uma senha: ")
        email = input("\nDigite um email: ")

        cursor.execute(
            "SELECT * FROM usuario WHERE email = %s and senha = %s",
            (email, senha)
        )

        usuario_encontrado = cursor.fetchone()

        if usuario_encontrado is None:
            print("\nEmail ou senha incorretos!")
        else:
            print("\nLogin realizado!")

    elif opcao == "3":
        usuarios = listar("usuario")
        for usuario in usuarios:
            print(usuario)        

    elif opcao == "4":
        id_usuario = int(input("Digite o ID: "))

        excluir("usuario", id_usuario)
        print("\nUsuario excluído!")

    elif opcao == "5":
        id_usuario = int(input("Digite um id: "))

        print("1. Nome: ")
        print("2. Senha: ")
        print("3. Email: ")

        campo =  input("O que deseja alterar? ")

        if campo == "1":
            coluna = "nome"
        elif campo == "2":
            coluna = "senha"
        elif campo == "3":
            coluna = "email"
        else: 
            print("Opção invalida!")
            continue

        novo_valor = input("Digite um novo valor: ")

        atualizar("usuario", coluna, novo_valor, id_usuario)
        print("usuario atualizado!")


        
    elif opcao == "6":
        print("\nSaindo do sistema!")
        break

    else:
        print("\nOpção inválida!")

cursor.close()
conexao.close()

print("\nConexão encerrada!")