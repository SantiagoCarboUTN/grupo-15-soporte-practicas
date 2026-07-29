import os
import json
from flask import Flask, render_template, request, redirect, url_for
from models import db, Shoe, Activity

def create_app():
    app = Flask(__name__)
    
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'tracker.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # ------------------- RUTAS DE INTERFAZ WEB -------------------

    # Vista 1: Dashboard Principal
    @app.get('/')
    def index():
        # Traemos las actividades ordenadas de más reciente a más antigua
        activities = Activity.query.order_by(Activity.date.desc()).all()
        shoes = Shoe.query.all()
        
        # Preparamos los datos para los gráficos (en orden inverso, cronológico)
        chart_data = []
        for act in reversed(activities):
            # Evitamos división por cero si alguien carga una distancia de 0
            ritmo_decimal = act.duration_minutes / act.distance_km if act.distance_km > 0 else 0
            
            chart_data.append({
                'fecha': act.date.strftime('%d/%m'),
                'distancia': act.distance_km,
                'ritmo': round(ritmo_decimal, 2)
            })
            
        # Convertimos la lista de Python a un string JSON seguro para JavaScript
        chart_data_json = json.dumps(chart_data)

        return render_template(
            'index.html', 
            activities=activities, 
            shoes=shoes, 
            chart_data=chart_data_json
        )

    # Vista 2: Formulario e Inserción de nueva actividad
    @app.route('/actividad/nueva', methods=['GET', 'POST'])
    def nueva_actividad():
        if request.method == 'POST':
            shoe_id = request.form.get('shoe_id')
            shoe_id = int(shoe_id) if shoe_id else None
            distance = float(request.form.get('distance_km'))
            
            new_activity = Activity(
                title=request.form.get('title'),
                distance_km=distance,
                duration_minutes=float(request.form.get('duration_minutes')),
                shoe_id=shoe_id
            )
            db.session.add(new_activity)
            
            # Sumamos los kilómetros a la zapatilla
            if shoe_id:
                shoe = Shoe.query.get(shoe_id)
                if shoe:
                    shoe.current_mileage += distance
                    
            db.session.commit()
            return redirect(url_for('index'))
            
        # Si es GET, cargamos la lista de calzado disponible
        shoes = Shoe.query.all()
        return render_template('nueva_actividad.html', shoes=shoes)

    # Vista 3: Formulario e Inserción de nueva zapatilla
    @app.route('/zapatilla/nueva', methods=['GET', 'POST'])
    def nueva_zapatilla():
        if request.method == 'POST':
            new_shoe = Shoe(
                brand=request.form.get('brand'),
                model_name=request.form.get('model_name'),
                max_mileage=float(request.form.get('max_mileage', 600.0))
            )
            db.session.add(new_shoe)
            db.session.commit()
            
            return redirect(url_for('index'))
            
        return render_template('nueva_zapatilla.html')

    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)