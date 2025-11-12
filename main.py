from menu import menu
from auth import is_logged_in, login_form
from banco import iniciar_database

if __name__ == "__main__":
    # Inicializar banco de dados (já inclui tabela de usuários)
    iniciar_database()

    if not is_logged_in():

        login_form()
    else:
        
        menu()