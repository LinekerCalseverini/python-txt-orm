# python-txt-orm
Módulo para Manipulação de TXT com Object Relational Mapping (ORM)

# Exemplo
```
import txt_orm


# Criação da classe do modelo
class Cliente(txt_orm.Model):
    __fields__ = ['id_', 'nome']


# Criação da classe da tabela
class TabelaClientes(txt_orm.TextDB):
    __fields__ = {
        'id_': 5,
        'nome': 19
    }
    __model__ = Cliente


# Instanciação do Banco
db = TabelaClientes('text.txt')

# Inserção de dados - CREATE
new_cliente = Cliente(id_='456', nome='Jeremias')
db.insert(new_cliente)

new_cliente2 = Cliente(id_='999', nome='Absinto Jefferson')
db.insert(new_cliente2)

new_cliente3 = Cliente(id_='817', nome='José da Silva Mendes de Oliveira')
db.insert(new_cliente3)

# Confirmação de alterações
db.commit()

# Seleção de um único registro - READ
jose = db.get(4)

# Atualização de Dados - UPDATE
jose.id_ = '222'
jose.nome = 'Robervaldo'
db.commit()

# Seleção de registros com filtros - READ
duplicatas = db.select(nome='José', id_='817')
print(duplicatas)

```
