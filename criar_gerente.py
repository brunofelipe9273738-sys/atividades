
import bcrypt
from projeto import BancoDados

banco = BancoDados()
banco.conectar()

login = "gerente"
senha = "123456"

senha_hash = bcrypt.hashpw(
    senha.encode(),
    bcrypt.gensalt()
).decode()

banco.executar(
    "INSERT INTO usuarios (login, senha_hash, perfil, ativo) VALUES (%s, %s, %s, %s)",
    (login, senha_hash, "GERENTE", 1)
)

print("Gerente criado com sucesso!")

banco.fechar()
