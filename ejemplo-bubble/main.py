from kivy.app import App
from kivy.uix.floatlayout import FloatLayout

class EjemploBubbe(App):
    def build(self):
        # Retorna el contenedor principal definido en el .kv
        return FloatLayout()

if __name__ == '__main__':
    EjemploBubble().run()