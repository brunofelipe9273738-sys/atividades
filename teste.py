import mysql.connector

conexao = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database=""
)
cursor = conexao.cursor()

while True:
    opcao = input("\n1 Cadastrar | 2 Login | 3 Listar | 4 Excluir | 5 Atualizar | 6 Sair: ")

    if opcao == "1":
        nome = input("Nome: ")
        senha = input("Senha: ")
        email = input("Email: ")
        cursor.execute(
            "INSERT INTO usuario (nome,senha,email) VALUES (%s,%s,%s)",
            (nome, senha, email)
        )
        conexao.commit()

    elif opcao == "2":
        cursor.execute(
            "SELECT * FROM usuario WHERE email=%s AND senha=%s",
            (input("Email: "), input("Senha: "))
        )
        print("Login OK!" if cursor.fetchone() else "Erro!")

    elif opcao == "3":
        cursor.execute("SELECT * FROM usuario")
        for usuario in cursor.fetchall():
            print(usuario)

    elif opcao == "4":
        cursor.execute(
            "DELETE FROM usuario WHERE id=%s",
            (input("ID: "),)
        )
        conexao.commit()

    elif opcao == "5":
        id_usuario = input("ID: ")
        campo = input("Campo: nome, senha ou email: ")

        if campo in ["nome", "senha", "email"]:
            cursor.execute(
                f"UPDATE usuario SET {campo}=%s WHERE id=%s",
                (input("Novo valor: "), id_usuario)
            )
            conexao.commit()

    elif opcao == "6":
        break

cursor.close()
conexao.close()