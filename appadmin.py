from flask import Blueprint, render_template, session, redirect, url_for
import __main__  

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/admin/panel')
def panel_administrador():
    
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
        
    try:
        
        Alumno = __main__.Alumno
        
        
        total_alumnos = Alumno.query.count()
        alumnos_con_rostro = Alumno.query.filter(Alumno.face_encoding.isnot(None)).count()
        
    except Exception as e:
        print("Error al consultar métricas:", e)
        total_alumnos = 0
        alumnos_con_rostro = 0
    
   
    return render_template('panelAdministrador.html', 
                           total_alumnos=total_alumnos, 
                           alumnos_con_rostro=alumnos_con_rostro)