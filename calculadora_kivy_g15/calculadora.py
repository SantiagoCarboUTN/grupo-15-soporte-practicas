import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
class RootWidget(BoxLayout):
  def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.numero_actual = ''
        self.primer_numero = None
        self.operacion     = None

  def presionar_numero(self, num):
      if self.numero_actual == '0' or self.numero_actual == '':
          self.numero_actual = num
      else:
          self.numero_actual += num
      self.ids.display.text = self.numero_actual

  def presionar_operacion(self, op):
      if op == 'igual':
          if self.primer_numero is not None and self.numero_actual != '':
              a = self.primer_numero
              b = int(self.numero_actual)
              resultado = a + b if self.operacion == 'suma' else a - b
              self.ids.display.text = str(resultado)
              self.primer_numero = None
              self.operacion     = None
              self.numero_actual = str(resultado)
      else:
          if self.numero_actual != '':
              self.primer_numero = int(self.numero_actual)
              self.operacion     = op
              self.numero_actual = ''
              self.ids.display.text = '0'

  def limpiar(self):
      self.numero_actual = ''
      self.primer_numero = None
      self.operacion     = None
      self.ids.display.text = '0'

class calculadora_widgets(App):
  def build(self):
        return RootWidget()

if __name__ == '__main__':
  calculadora_widgets().run()