import mysql.connector

conexao = mysql.connector.connect(
host = "localhost", 
user = "root",
password = "",
database = "banco_bd"
)

#CRUD GENERICO

def cadastrar(tabela,colunas,valores):
    campos = ','.join(colunas)
    parametros = ','.join(['%s'] * len(valores))

    sql = f"INSERT INTO {tabela} ({campos}) VALUES ({parametros})"

    cursor.execute(sql, valores)
    conexao.commit()

def listar(tabela):
    sql = f"SELECT * FROM {tabela}"

    cursor.execute(sql)
    return cursor.fetchall()

def atualizar(  tabela, coluna, valor, id_registrado):
    sql = f"UPDATE {tabela} SET {coluna} = %s WHERE id = %s"

    cursor.execute(sql, (valor, id_registrado))
    conexao.commit()


def excluir(tabela, id_registrado):
    sql = f"DELETE FROM {tabela} WHERE id = %s"

    cursor.execute(sql, (id_registrado,))
    conexao.commit()
    
cursor = conexao.cursor()


#MENU PRINCIPAL

while True:
    print("\n===== MENU PRINCIPAL ===== ")
    print("1. Cadastrar usuário: ")
    print("2. Fazer Login: ")
    print("3. Listar usúarios")
    print("4. Atualizar usúario")
    print("5. Excluir usúario")
    print("6. Sair")

    opcao = input("Escolha uma opção: ")


    #cadastro de usuário
    if opcao == "1":
        nome_usuario = input("Digite o nome do usuário: ")
        senha = input("Digite a senha: ")
        email = input("Digite o email: ")

        cadastrar(
            "usuario",
            ["nome", "senha", "email"],
            [nome_usuario, senha, email]
        )

        print("Usuário cadastrado com sucesso!")


        #login de usuário
    elif opcao == "2":
        senha = input("Digite a senha: ")
        email = input("Digite o email: ")


        cursor.execute(
            "SELECT * FROM usuario WHERE email = %s and senha = %s",
            (email, senha)
        )

        usuario_encontrado = cursor.fetchone()

        if usuario_encontrado is None:
            print("Email ou senha incorretos!")
        else:
            print("Login realizado com sucesso!")


    #sair do programa
    elif opcao == "3":
        usuarios = listar("usuario")

        for usuario in usuarios:
            print(usuario)
    
    
    #atualizar usuario
    elif opcao == "4":
        id_usuario = int(input("Digite o ID do usúario: "))
        novo_nome = input("Digite o novo nome: ")

        atualizar("usuario", "nome", novo_nome, id_usuario)

        print("Usúario atualizado!")



    #excluir usuario
    elif opcao == "5":
        id_usuario = int(input("Digite o ID do usúario: "))

        excluir("usuario", id_usuario)

        print("Usúario excluído!")
        
    #sair
    elif opcao =="6":
        print("Saindo do sistema...")
        break

    else:
        print("Opção inválida!")


cursor.close()
conexao.close()

print("Conexão encerrada.")