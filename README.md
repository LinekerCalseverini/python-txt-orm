# python-txt-orm
Módulo para Manipulação de TXT com Object Relational Mapping (ORM)

# Exemplo
```
import txt_orm
from txt_orm.fields import CharField, PositiveIntegerField


# Criação da classe do modelo
class Cliente(txt_orm.Model):
    __fields__ = {
        'nome': CharField(size=50),
        'idade': PositiveIntegerField()
    }


# Criação da classe da tabela
class TabelaClientes(txt_orm.TextDB):
    __model__ = Cliente


# Instanciação do Banco
db = TabelaClientes('text.txt')

# Inserção de dados - CREATE
new_cliente = Cliente(nome='Jeremias', idade=25)
db.insert(new_cliente)

new_cliente2 = Cliente(nome='Absinto Jefferson', idade=28)
db.insert(new_cliente2)

new_cliente3 = Cliente(nome='José da Silva Mendes de Oliveira', idade=37)
db.insert(new_cliente3)

new_cliente4 = Cliente(nome='Robervaldo', idade=42)
db.insert(new_cliente3)

# Confirmação de alterações
db.commit()

# Seleção de um único registro - READ
jose = db.get(3)
if jose is None:
    exit(0)

# Atualização de Dados - UPDATE
jose.nome = 'Robervaldo'
jose.idade = 39
db.commit()

# Seleção de registros com filtros - READ
duplicatas = db.select(nome='Robervaldo')

for duplicata in duplicatas:
    print(duplicata)

```
