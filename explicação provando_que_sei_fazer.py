# ANOTAÇÕES – SISTEMA BANCÁRIO
**Assunto:** Explicação das principais partes do código

---

### 1. CONEXÃO COM O BANCO DE DADOS

**Código:**
```python
def conectar(self):
    self.conexao = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="trabalho_banco"
    )
    self.cursor = self.conexao.cursor()
```

**Explicação:**

- Conecta o Python ao banco de dados MySQL.
- `mysql.connector`: permite a comunicação entre Python e MySQL.
- `cursor`: executa comandos SQL e recebe informações do banco.

### 2. PROTEÇÃO DE SENHAS – BCRYPT

**Código:**
```python
senha = bcrypt.hashpw(
    senha.encode(), bcrypt.gensalt()
).decode()
```

**Explicação:**

- Utiliza a biblioteca Bcrypt para proteger as senhas.
- Transforma a senha em um hash antes de armazená-la.
- Assim, a senha original não fica salva diretamente no banco de dados.

### 3. HERANÇA – POO

**Código:**
```python
class Gerente(Usuario):
```

```python
class Cliente(Usuario):
    def __init__(self, id_usuario, login, perfil, senha_hash, id_cliente):
        super().__init__(id_usuario, login, perfil, senha_hash)
```

**Explicação:**

- Utiliza o conceito de herança da Programação Orientada a Objetos.
- `Usuario` é a classe principal.
- `Gerente` e `Cliente` herdam características da classe `Usuario`.
- Isso evita repetir partes do código.

### 4. VALIDAÇÃO DE SALDO E MOVIMENTAÇÕES

**Código:**
```python
if valor <= 0 or (tipo == "SAQUE" and valor > saldo):
    raise Exception("Valor inválido ou saldo insuficiente!")
```

**Explicação:**

- Verifica se o valor da operação é válido.
- Impede depósitos e saques com valores menores ou iguais a zero.
- Também impede saques maiores que o saldo disponível.
- Evita operações bancárias inválidas.

### 5. TRANSFERÊNCIAS – COMMIT E ROLLBACK

**Código:**
```python
self.banco.conexao.commit()

except Exception:
    self.banco.conexao.rollback()
    raise
```

**Explicação:**

- `commit`: confirma as alterações no banco de dados.
- `rollback`: desfaz as alterações caso aconteça algum erro.
- Esses comandos ajudam a garantir que uma transferência não seja concluída pela metade.

---

## PONTOS IMPORTANTES PARA A APRESENTAÇÃO

**Bcrypt:** proteção das senhas.

**Herança:** reutilização de código entre as classes.

**MySQL:** armazenamento das informações.

**Validações:** controle das operações bancárias.

**Commit e Rollback:** segurança nas transferências.

---

**Objetivo:** compreender como cada parte funciona e conseguir explicar ao professor por que ela foi utilizada no projeto.
