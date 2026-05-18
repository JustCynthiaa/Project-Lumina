from datetime import datetime
from flask import Blueprint, jsonify, render_template, session, redirect, url_for
from models import db, Alumno, Entradas     #ahora importamos desde models

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/admin/panel')
def panel_administrador():
    
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
        
    try:
        
        total_alumnos = Alumno.query.count()
        alumnos_con_rostro = Alumno.query.filter(Alumno.face_encoding.isnot(None)).count()
        entradas_hoy = Entradas.query.filter(Entradas.fecha_hora >= datetime.now().date()).count()  #es redundante pero shh
        lista_entradas = db.session.query(Entradas, Alumno).join(Alumno, Entradas.no_control == Alumno.no_control).filter(Entradas.fecha_hora >= datetime.now().date()).order_by(Entradas.fecha_hora.desc()).all()
        
    except Exception as e:
        print("Error al consultar métricas:", e)
        total_alumnos = 0
        alumnos_con_rostro = 0
        entradas_hoy = 0
   
    return render_template('panelAdministrador.html', 
                           total_alumnos=total_alumnos, 
                           alumnos_con_rostro=alumnos_con_rostro,
                           entradas_hoy=entradas_hoy,
                           lista_entradas=lista_entradas)
@admin_bp.route('/admin/api/avanzar_semestres', methods=['POST'])
def avanzar_semestres():
    """Aumenta en 1 el semestre de todos los alumnos registrados."""
    if not session.get('admin_logged_in'):
        return jsonify({'exito': False, 'mensaje': 'No autorizado'}), 401

    try:
        alumnos = Alumno.query.all()
        actualizados = 0
        
        for al in alumnos:
           if al.semestre and al.semestre.isdigit():
                sem_actual = int(al.semestre)
                # limite de 15 porque si
                if sem_actual < 15:
                    al.semestre = str(sem_actual + 1)
                    actualizados += 1
        
        db.session.commit()
        return jsonify({
            'exito': True, 
            'mensaje': f'Se avanzó exitosamente el semestre de {actualizados} alumnos.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'exito': False, 'mensaje': str(e)})