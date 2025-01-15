import base64
from io import BytesIO
from PIL import Image, ExifTags
from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from flask_cors import CORS
from collections import OrderedDict
import datetime
import hashlib
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity,decode_token
)


app = Flask(__name__)
CORS(app)  # Aplica CORS a toda la aplicación

app.config['MYSQL_HOST'] = '167.71.118.217' 
app.config['MYSQL_USER'] = 'admin_flutt'
app.config['MYSQL_PASSWORD'] = 'lOtTetiz8P'
app.config['MYSQL_DB'] = 'admin_flutt'
app.config["JWT_SECRET_KEY"] = "1234"  # Cambia esta clave
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limita el tamaño del archivo a 16 MB
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']
jwt = JWTManager(app)

mysql = MySQL(app)

# Ruta para obtener todos los usuarios de la tabla 'usuarios'
@app.route("/usuarios", methods=['GET'])
@jwt_required()
def get_usuarios():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users')
        usuarios = cursor.fetchall()
        cursor.close()

        usuarios_json = [{'id_users': usuario[0], 'nombreUser': usuario[1], 'apellido': usuario[2], 'email': usuario[3], 'password': usuario[4], 'depto': usuario[5], 'tipo_usuario': usuario[6]} for usuario in usuarios]
        return jsonify(usuarios_json), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    
@app.route("/deptos", methods=['GET'])
@jwt_required()
def get_deptos():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT depto FROM users')
        usuarios = cursor.fetchall()
        cursor.close()

        usuarios_json = [{'depto': usuario[0]} for usuario in usuarios]
        return jsonify(usuarios_json), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@app.route('/usr', methods=['POST'])
def index():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'status': 'error', 'message': 'Email y password son requeridos.'}), 400

        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
        usuario = cur.fetchone()

        if not usuario:
            return jsonify({'status': 'not_found', 'message': 'Email o contraseña incorrectos.'}), 404

        access_token = create_access_token(identity=email)

        cur.execute('UPDATE users SET token = %s WHERE email = %s', (access_token, email))
        mysql.connection.commit()

        usuario_json = {
            'id_users': usuario[0],
            'nombreUser': usuario[1],
            'apellido': usuario[2],
            'email': usuario[3],
            'depto': usuario[6],
            'telefono': usuario[7],
            'tipo_usuario': usuario[8]

        }

        return jsonify({'status': 'success', 'access_token': access_token, 'user_data': usuario_json}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error del servidor: {str(e)}'}), 500

@app.route('/modificarPerfil', methods=['POST'])
@jwt_required()
def modPerfil():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        telefono = data.get('telefono')
        nombre = data.get('nombre')
        apellido = data.get('apellido')

        if not email:
            return jsonify({'status': 'error', 'message': 'El email es obligatorio'}), 400

        # Construir dinámicamente la consulta
        campos_a_actualizar = []
        valores = []

        if nombre:
            campos_a_actualizar.append("nombreUser=%s")
            valores.append(nombre)
        if telefono:
            campos_a_actualizar.append("telefono=%s")
            valores.append(telefono)
        if password:
            campos_a_actualizar.append("password=%s")
            valores.append(password)
        if apellido:
            campos_a_actualizar.append("apellido=%s")
            valores.append(apellido)

        if not campos_a_actualizar:
            return jsonify({'status': 'error', 'message': 'No se proporcionaron campos para actualizar'}), 400
        print(campos_a_actualizar)
        # Agregar el email a los valores y construir la consulta
        valores.append(email)
        consulta = f"UPDATE users SET {', '.join(campos_a_actualizar)} WHERE email=%s"

        # Ejecutar la consulta
        cur = mysql.connection.cursor()
        cur.execute(consulta, valores)
        mysql.connection.commit()

        return jsonify({'status': 'success', 'message': 'Usuario modificado con éxito'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error del servidor: {str(e)}'}), 500


@app.route('/validarToken', methods=['POST'])
def validar_token():
    data = request.json
    token = data.get("token")

    if not token:
        return jsonify({"valid": False, "message": "Token no proporcionado"}), 400

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM users WHERE token = %s', (token,))
    usuario = cur.fetchone()
    usuario_json = {
            'id_users': usuario[0],
            'nombreUser': usuario[1],
            'apellido': usuario[2],
            'email': usuario[3],
            'depto': usuario[6],
            'telefono': usuario[7],
            'tipo_usuario': usuario[8]

    }

    try:
        # Decodifica el token usando `decode_token`
        decoded_token = decode_token(token)
        return jsonify({
            "valid": True,
            "message": "El token es válido.",
            "decoded_token": decoded_token,
            "user_data": usuario_json  # Opcional: muestra todo el token decodificado
        }), 200
        
    except Exception as e:
        # Maneja errores de decodificación
        return jsonify({
            "valid": False,
            "message": str(e)
        }), 401

@app.route('/validarToken2', methods=['POST'])
def validar_token2():
    data = request.json
    token = data.get("token")
    email = data.get("email")
    password = data.get("password")

    if not token:
        return jsonify({"valid": False, "message": "Token no proporcionado"}), 400
    if not email or not password:
            return jsonify({'status': 'error', 'message': 'Email y password son requeridos.'}), 400

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
    usuario = cur.fetchone()
    usuario_json = {
             'id_users': usuario[0],
            'nombreUser': usuario[1],
            'apellido': usuario[2],
            'email': usuario[3],
            'depto': usuario[6],
            'telefono': usuario[7],
            'tipo_usuario': usuario[8]

    }

    try:
        # Decodifica el token usando `decode_token`
        decoded_token = decode_token(token)
        return jsonify({
            "valid": True,
            "message": "El token es válido.",
            "decoded_token": decoded_token,
            "user_data": usuario_json  # Opcional: muestra todo el token decodificado
        }), 200
    except Exception as e:
        # Maneja errores de decodificación
        return jsonify({
            "valid": False,
            "message": str(e)
        }), 401

@app.route('/eliminarInvitado', methods=['POST'])
@jwt_required()
def del_inv():
    data = request.json
    id_inv = data.get('id_inv')
    
    if not id_inv:
        return jsonify({"error": "El campo 'id_inv' es obligatorio"}), 400
    
    try:
        cur = mysql.connection.cursor()
        
        cur.execute('SELECT * FROM invitados WHERE id_inv = %s', (id_inv,))
        invitado = cur.fetchone()
        
        if not invitado:
            return jsonify({"error": "No se encontró el invitado con id proporcionado"}), 404
        
        # Eliminar al invitado
        cur.execute('DELETE FROM invitados WHERE id_inv = %s', (id_inv,))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({"message": "El invitado ha sido eliminado exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": f"Error al procesar la solicitud: {str(e)}"}), 500


@app.route('/deshabilitarQr', methods=['POST'])
@jwt_required()
def qr_deshabilitado():
    try:
        # Obtener datos del cuerpo JSON
        data = request.json
        id_inv = data.get('id_inv')

        # Validar datos
        if not id_inv:
            return jsonify({'status': 'invalid_request', 'message': 'El ID del invitado es requerido.'}), 400

        # Consultar si el invitado existe y si está habilitado
        with mysql.connection.cursor() as cur:
            cur.execute('SELECT habilitado FROM invitados WHERE id_inv = %s', (id_inv,))
            invitado = cur.fetchone()

            if invitado is None:
                return jsonify({'status': 'not_found', 'message': 'No se encontró el invitado.'}), 404

            habilitado = invitado[0]
            if habilitado == 0:
                return jsonify({'status': 'qr_already_disabled', 'message': 'Este QR ya está deshabilitado.'}), 200

            # Deshabilitar el QR (habilitado = 0)
            cur.execute('UPDATE invitados SET habilitado = 0 WHERE id_inv = %s', (id_inv,))
            mysql.connection.commit()

        return jsonify({'status': 'success', 'message': 'QR deshabilitado correctamente.'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Ocurrió un error: {str(e)}'}), 500


@app.route('/generarInvitados', methods=['POST'])
@jwt_required()
def generarInv():
    data = request.json
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    depto = data.get('depto')
    habilitado= 1
    cur = mysql.connection.cursor()
    try:
        cur.execute('INSERT INTO invitados (nombre, apellido, depto, habilitado) VALUES (%s, %s, %s, %s)', (nombre, apellido, depto, habilitado))
        mysql.connection.commit()
        return jsonify({'message': 'Se ingresó correctamente'}), 201
    except Exception as e:
        mysql.connection.rollback()                  
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        
@app.route('/generarInvitadosMRZ', methods=['POST'])
@jwt_required()
def generarInv2():
    data = request.json
    nombre = data.get('nombre')
    tipo_doc= data.get('tipo_doc')
    numero_doc= data.get('numero_doc')
    pais= data.get('pais')
    sexo= data.get('sexo')
    casa= data.get('casa')
    patente= data.get('patente')
    comentarios= data.get('comentarios')

    nombre_guardia= data.get('nombre_guardia')
    nom_porteria= 'porteria 1'

    cur = mysql.connection.cursor()
    try:
        cur.execute('INSERT INTO invitadosMrz (nombre, tipo_doc, numero_doc, pais, sexo,nombre_guardia, nom_porteria, casa, patente, comentarios) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (nombre,tipo_doc, numero_doc, pais, sexo,nombre_guardia,nom_porteria,casa, patente, comentarios))
        mysql.connection.commit()
        return jsonify({'message': 'Se ingresó correctamente'}), 201
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()


from PIL import Image, ExifTags
from io import BytesIO

def resize_image(image, max_size=(800, 800)):
    # Abrir la imagen
    img = Image.open(image)
    
    # Convertir a modo RGB si la imagen tiene un canal alfa
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    # Intentar ajustar la orientación según los metadatos EXIF
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = img._getexif()
        if exif is not None:
            exif = dict(exif.items())
            orientation = exif.get(orientation)
            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # Caso en que la imagen no tenga datos EXIF
        pass

    # Redimensionar la imagen manteniendo la relación de aspecto
    img.thumbnail(max_size)

    # Guardar la imagen redimensionada en un buffer
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    
    return buffer

@app.route('/generarLibroNovedades', methods=['POST'])
@jwt_required()
def generarNov():
    try:
        # Obtener los datos del formulario
        titulo = request.form.get('titulo')
        texto = request.form.get('texto')
        imagen_referencia1= request.files.get('image1')
        imagen_referencia2 = request.files.get('image2')
        imagen_referencia3 = request.files.get('image3')

        video = request.files.get('video')

        # Convertir imagen a base64 si existe
        image_base641 = None
        image_base642 = None
        image_base643 = None

        if imagen_referencia1:
            resized_image = resize_image(imagen_referencia1)
            image_base641 = base64.b64encode(resized_image.read()).decode('utf-8')
        if imagen_referencia2:
            resized_image = resize_image(imagen_referencia2)
            image_base642 = base64.b64encode(resized_image.read()).decode('utf-8')
        if imagen_referencia3:
            resized_image = resize_image(imagen_referencia3)
            image_base643 = base64.b64encode(resized_image.read()).decode('utf-8')

        # Convertir video a base64 si existe
        video_base64 = None
        if video:
            video_base64 = base64.b64encode(video.read()).decode('utf-8')

        # Crear cursor y consulta SQL
        cur = mysql.connection.cursor()
        sql_insert_query = """
            INSERT INTO libroNovedades (titulo, texto, img1,img2,img3, video) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        insert_tuple = (titulo, texto, image_base641,image_base642,image_base643, video_base64)
        
        # Ejecutar la consulta e insertar los datos
        cur.execute(sql_insert_query, insert_tuple)
        mysql.connection.commit()
        cur.close()

        return jsonify({'message': 'Se ingresó correctamente'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def resize_image2(file):
    try:
        image = Image.open(file)
        image.thumbnail((800, 800))  # Redimensionar si es necesario
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format=image.format)
        img_byte_arr.seek(0)
        return img_byte_arr
    except Exception as e:
        print("Error al redimensionar la imagen:", str(e))
        raise e

@app.route('/generarReportes', methods=['POST'])
def generarRep():
    try:
        # Obtener los datos del formulario
        nombre = request.form.get('nombre')
        ubicacion = request.form.get('ubicacion')
        descripcion = request.form.get('descripcion')
        imagen_referencia = request.files.get('image')

        # Validar la imagen
        if imagen_referencia and imagen_referencia.filename:
            resized_image = resize_image(imagen_referencia)
            image_base64 = base64.b64encode(resized_image.read()).decode('utf-8')
        else:
            image_base64= None

        # Insertar los datos en la base de datos MySQL
        cur = mysql.connection.cursor()
        sql_insert_query = "INSERT INTO reportes (nombre, ubicacion, descripcion, image) VALUES (%s, %s, %s, %s)"
        insert_tuple = (nombre, ubicacion, descripcion, image_base64)
        cur.execute(sql_insert_query, insert_tuple)
        mysql.connection.commit()
        cur.close()

        return jsonify({'message': 'Se ingresó correctamente'}), 201

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': str(e)}), 500



@app.route('/generarCasilla', methods=['POST'])
#@jwt_required()
def generarCass():
    try:
        # Obtener los datos del formulario
        data = request.get_json()
        depto = data.get('depto')
        descripcion = data.get('descripcion')
        imagen_referencia = request.files.get('image')

        if imagen_referencia and imagen_referencia.filename:
            resized_image = resize_image(imagen_referencia)
            image_base64 = base64.b64encode(resized_image.read()).decode('utf-8')
        else:
            image_base64= None


        # Insertar los datos en la base de datos MySQL
        cur = mysql.connection.cursor()
        sql_insert_query = "INSERT INTO casilla (depto, descripcion ,image) VALUES ( %s, %s, %s)"
        insert_tuple = (depto,descripcion, image_base64)
        cur.execute(sql_insert_query, insert_tuple)
        mysql.connection.commit()
        cur.close()
        print(request.content_type)  # Debe ser 'multipart/form-data'

        return jsonify({'message': 'Se ingresó correctamente'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generarUsuario', methods=['POST'])
@jwt_required()
def generarUsr():
    try:
        # Obtener los datos del formulario
        nombre= request.form.get('nombre')
        apellido= request.form.get('apellido')
        email= request.form.get('email')
        depto= request.form.get('depto')
        password= request.form.get('password')
        tipo_usuario= request.form.get('tipo_usuario')
        tipo_usuario = int(request.form.get('tipo_usuario', 0))  
        h = hashlib.md5(password.encode()).hexdigest()
        if tipo_usuario==2:
            onboarding=1
        else:
            onboarding=0

        # Insertar los datos en la base de datos MySQL
        cur = mysql.connection.cursor()
        sql_insert_query = "INSERT INTO users (nombreUser, apellido, email, depto, password,onboarding, tipo_usuario) VALUES ( %s, %s, %s,%s, %s, %s, %s)"
        insert_tuple = (nombre,apellido,email, depto,h,onboarding, tipo_usuario)
        cur.execute(sql_insert_query, insert_tuple)
        mysql.connection.commit()
        cur.close()

        return jsonify({'message': 'Se ingresó correctamente'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generarLibroNovedades', methods=['POST'])
@jwt_required()
def generarLib():
    try:
        # Obtener los datos del formulario
        texto= request.form.get('texto')
        imagen_referencia = request.files.get('image')

        resized_image = resize_image(imagen_referencia)
        image_base64 = base64.b64encode(resized_image.read()).decode('utf-8')

        # Insertar los datos en la base de datos MySQL
        cur = mysql.connection.cursor()
        sql_insert_query = "INSERT INTO libroNovedades (texto, img) VALUES ( %s, %s)"
        insert_tuple = (texto, image_base64)
        cur.execute(sql_insert_query, insert_tuple)
        mysql.connection.commit()
        cur.close()

        return jsonify({'message': 'Se ingresó correctamente'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/libroNovedades', methods=['GET'])
@jwt_required()
def api_libro_novedades():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM libroNovedades ORDER BY id_lib DESC')
        invitados = cursor.fetchall()
        cursor.close()

        invitado_json = [
            OrderedDict([
                ('id_lib', invitado[0]),        
                ('texto', invitado[1]),        
                ('img', invitado[2]),  
                ('fecha_creacion', invitado[3])
            ])
            for invitado in invitados
        ]
        return jsonify(invitado_json), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@app.route('/generarNoticias', methods=['POST'])
@jwt_required()
def generarNot():
    try:
        # Obtener los datos del formulario
        titulo = request.form.get('titulo')
        bajada = request.form.get('bajada')
        cuerpo = request.form.get('cuerpo')

        # Verificar si se recibe el archivo correctamente
        imagen_referencia = request.files.get('image')
        if imagen_referencia is None:
            return jsonify({'error': 'No se recibió ninguna imagen'}), 400

        resized_image = resize_image(imagen_referencia)  # Verifica si resize_image está funcionando correctamente
        image_base64 = base64.b64encode(resized_image.read()).decode('utf-8')

        # Insertar los datos en la base de datos MySQL
        cur = mysql.connection.cursor()
        sql_insert_query = "INSERT INTO noticias (titulo, bajada, cuerpo, image) VALUES (%s, %s, %s, %s)"
        insert_tuple = (titulo, bajada, cuerpo, image_base64)
        cur.execute(sql_insert_query, insert_tuple)
        mysql.connection.commit()
        cur.close()

        return jsonify({'message': 'Se ingresó correctamente'}), 201

    except Exception as e:
        print(f"Error en : {e}")

        # Capturar el error y devolverlo en la respuesta
        return jsonify({'error': str(e)}), 500

    
@app.route('/noticias', methods=['GET'])
@jwt_required()
def api_noticias():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM noticias ORDER BY id_not DESC')
        invitados = cursor.fetchall()
        cursor.close()

        invitado_json = [
            OrderedDict([
                ('id_not', invitado[0]),        
                ('titulo', invitado[1]),        
                ('bajada', invitado[2]),  
                ('cuerpo', invitado[3]),  
                ('img', invitado[4]),  
                ('fecha_creacion', invitado[5])
            ])
            for invitado in invitados
        ]
        return jsonify(invitado_json), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    
@app.route('/invitados', methods=['GET'])
@jwt_required()
def api_get_invitados():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM invitados ORDER BY id_inv DESC')
        invitados = cursor.fetchall()
        cursor.close()

        invitado_json = [
            OrderedDict([
                ('id_inv', invitado[0]),        
                ('nombre', invitado[1]),    
                ('apellido', invitado[2]),        
                ('rut', invitado[3]),  
                ('depto', invitado[4]),  
                ('fecha_creacion', invitado[5]),
                ('fecha_expiracion', invitado[7])

            ])
            for invitado in invitados
        ]
        return jsonify(invitado_json), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    
@app.route('/invitadosMrz', methods=['GET'])#arreglar
@jwt_required()
def api_get_invitadosMrz():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM invitadosMrz ORDER BY id_inv DESC')
        invitados = cursor.fetchall()
        cursor.close()

        invitado_json = [
            OrderedDict([
                ('nombre', invitado[1]),        
                ('tipo_doc', invitado[2]),  
                ('numero_doc', invitado[3]), 
                ('pais', invitado[4]),  
                ('sexo', invitado[5]),  
                ('nombre_guardia', invitado[6]),  
                ('casa', invitado[8]),  
                ('patente', invitado[9]),  
                ('comentarios', invitado[10]),  
                ('fecha_creacion', invitado[11]),  

            ])
            for invitado in invitados
        ]
        return jsonify(invitado_json), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
def serialize_timedelta(obj):
    if isinstance(obj, datetime.timedelta):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def formatoFecha(obj):
    return obj.strftime("%Y/%m/%d")

@app.route('/generarAmenities', methods=['POST'])
@jwt_required()
def generarAmen():
    data = request.json
    nombre = data.get('nombre')
    fecha = data.get('fecha')
    hora_entrada = data.get('hora_entrada')
    descripcion = data.get('descripcion')
    hora_salida = data.get('hora_salida')

    cur = mysql.connection.cursor()
    try:
        cur.execute('INSERT INTO `amenities`(`nombre`, `descripcion`, `fecha`, `hora_entrada`, `hora_salida`) VALUES (%s, %s, %s, %s, %s)', (nombre, descripcion,fecha, hora_entrada, hora_salida))
        mysql.connection.commit()
        return jsonify({'message': 'Se ingresó correctamente'}), 201
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()

@app.route('/horasAmenities', methods=['GET'])
@jwt_required()
def api_get_amenities():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM amenities ORDER BY id_ame DESC')
        amenities = cursor.fetchall()
        cursor.close()

        amenities_json = [
            OrderedDict([
                ('id_ame', amenitie[0]),        
                ('nombre', amenitie[1]),        
                ('descripcion', amenitie[2]),  
                ('fecha', formatoFecha(amenitie[3])),  
                ('hora_entrada', str(amenitie[4]) if isinstance(amenitie[4], datetime.timedelta) else amenitie[4]),
                ('hora_salida', str(amenitie[5]) if isinstance(amenitie[5], datetime.timedelta) else amenitie[5]),
                ('fecha_creacion', amenitie[6])

                
            ])
            for amenitie in amenities
        ]
        return jsonify(amenities_json), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500


@app.route('/reportes', methods=['GET'])
#@jwt_required()
def api_get_reportes():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM reportes ORDER BY id_rep DESC')
        reportes = cursor.fetchall()
        cursor.close()

        reporte_json = [
            OrderedDict([
                ('id_rep', reporte[0]),        
                ('nombre', reporte[1]),        
                ('ubicacion', reporte[2]),
                ('descripcion', reporte[3]),
                ('image', reporte[4]),
                ('fecha_creacion', reporte[5]),


            ])
            for reporte in reportes
        ]
        return jsonify(reporte_json), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    
@app.route('/casillas', methods=['GET'])
@jwt_required()
def api_get_casillas():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM casilla ORDER BY id_cas DESC')
        reportes = cursor.fetchall()
        cursor.close()

        reporte_json = [
            OrderedDict([
                ('id_cas', reporte[0]),        
                ('depto', reporte[1]),        
                ('descripcion', reporte[2]),
                ('image', reporte[3])    

            ])
            for reporte in reportes
        ]
        return jsonify(reporte_json), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
@app.route('/usr/modOnboarding', methods=['PUT'])
@jwt_required()
def update_onboarding():
    try:
        data = request.json
        id_usuario = data.get('id_usuario')

        if not id_usuario:
            return jsonify({'error': 'ID de usuario no proporcionado'}), 400

        cur = mysql.connection.cursor()
        cur.execute('UPDATE users SET onboarding = 1 WHERE id_users = %s', (id_usuario,))
        mysql.connection.commit()

        if cur.rowcount > 0:
            return jsonify({'message': 'Estado de onboarding actualizado correctamente'}), 200
        else:
            return jsonify({'message': 'No se encontró el usuario con el ID proporcionado'}), 404
    except Exception as e:
        print('Error en la actualización de onboarding:', str(e))
        return jsonify({'error': f'Error en la actualización de onboarding: {str(e)}'}), 500
    finally:
        cur.close()

if __name__ == '__main__':
    app.run(debug=True)
