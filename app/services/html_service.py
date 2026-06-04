# app/services/html_service.py
from datetime import datetime

def generar_html_confirmacion(nombre: str, apellido: str, email: str, telefono: str, codigo: str, ya_existia: bool = False):
    dominio = email.split('@')[1]
    
    mensaje_existente = ""
    if ya_existia:
        mensaje_existente = """
        <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            ℹ️ Ya tienes un código de verificación activo. Usa el mismo código que te enviamos anteriormente.
        </div>
        """
    
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verificación DNS TXT - klbrs.es</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        .success-card {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 650px;
            width: 100%;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        .success-icon {{ font-size: 80px; color: #28a745; margin-bottom: 20px; }}
        h1 {{ color: #333; margin-bottom: 10px; }}
        h3 {{ color: #4a5568; margin-bottom: 10px; }}
        p {{ color: #666; margin-bottom: 20px; line-height: 1.6; }}
        .info-box {{
            background: #f0f7ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 20px 0;
            text-align: left;
            border-radius: 8px;
        }}
        .codigo-box {{
            background: #2d3748;
            color: #68d391;
            font-family: monospace;
            font-size: 14px;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            word-break: break-all;
        }}
        .button-group {{
            display: flex;
            gap: 15px;
            margin: 25px 0;
            flex-wrap: wrap;
            justify-content: center;
        }}
        .btn-validate {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 14px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }}
        .dropdown {{
            position: relative;
            display: inline-block;
        }}
        .btn-payment {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 14px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
            width: 100%;
        }}
        .dropdown-content {{
            display: none;
            position: absolute;
            background-color: white;
            min-width: 200px;
            box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
            border-radius: 10px;
            z-index: 1;
            top: 100%;
            left: 0;
            margin-top: 5px;
        }}
        .dropdown-content a {{
            color: #333;
            padding: 12px 16px;
            text-decoration: none;
            display: block;
            text-align: left;
            border-radius: 10px;
            cursor: pointer;
        }}
        .dropdown-content a:hover {{
            background-color: #f0f0f0;
        }}
        .dropdown:hover .dropdown-content {{
            display: block;
        }}
        .btn-validate:hover, .btn-payment:hover {{ transform: translateY(-2px); }}
        .btn-validate:disabled, .btn-payment:disabled {{ opacity: 0.6; cursor: not-allowed; transform: none; }}
        .resultado-box {{ margin-top: 20px; padding: 15px; border-radius: 10px; display: none; }}
        .resultado-success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
        .resultado-error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        .resultado-warning {{ background: #fff3cd; color: #856404; border: 1px solid #ffeeba; }}
        .resultado-info {{ background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }}
        .loading-spinner {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
            margin-right: 8px;
        }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        .btn-back {{
            display: inline-block;
            background: #6c757d;
            color: white;
            padding: 12px 24px;
            border-radius: 10px;
            text-decoration: none;
            margin-top: 10px;
        }}
        
        .auditoria-section {{
            margin-top: 30px;
            border-top: 2px solid #e2e8f0;
            padding-top: 20px;
            text-align: center;
        }}
        .resumen-grid {{
            display: flex;
            justify-content: space-around;
            margin: 15px 0;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .resumen-item {{
            padding: 12px 20px;
            border-radius: 8px;
            text-align: center;
            min-width: 90px;
        }}
        .resumen-criticas {{ background: #fed7d7; }}
        .resumen-medias {{ background: #feebc8; }}
        .resumen-bajas {{ background: #c6f6d5; }}
        .btn-auditar {{
            background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
            color: white;
            padding: 14px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin: 15px 0;
            transition: transform 0.2s ease;
        }}
        .btn-auditar:hover {{ transform: translateY(-2px); }}
        .btn-auditar:disabled {{ opacity: 0.6; cursor: not-allowed; transform: none; }}
        .btn-descargar {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            display: inline-block;
            font-weight: 600;
            margin-top: 10px;
        }}
        .btn-descargar:hover {{ transform: translateY(-2px); }}
        
        @media (max-width: 600px) {{
            .button-group {{ flex-direction: column; }}
            .btn-validate, .btn-payment, .dropdown {{ width: 100%; }}
            .dropdown-content {{
                position: relative;
                box-shadow: none;
                border: 1px solid #e0e0e0;
                margin-top: 5px;
            }}
            .success-card {{ padding: 25px; }}
        }}
    </style>
</head>
<body>
    <div class="success-card">
        <div class="success-icon">🔐</div>
        <h1>Verificación DNS TXT</h1>
        {mensaje_existente}
        <p>Hemos enviado un email a <strong>{email}</strong> con instrucciones.</p>
        
        <div class="codigo-box">
            <strong>Código de verificación:</strong><br>
            {codigo}
        </div>
        
        <div class="info-box">
            <strong>📝 ¿Qué debes hacer?</strong><br><br>
            1. Inicia sesión en el panel DNS de <strong>{dominio}</strong><br>
            2. Crea un nuevo registro <strong>TXT</strong><br>
            3. En el campo "Valor", pega EXACTAMENTE el código de arriba<br>
            4. Guarda los cambios<br>
            5. Espera 5-10 minutos a que se propague<br>
            6. Haz clic en <strong>"Validar DNS"</strong>
        </div>
        
        <div class="button-group">
            <button onclick="validarDNS()" id="btnValidar" class="btn-validate">🔍 Validar DNS</button>
            
            <div class="dropdown">
                <button id="btnPago" class="btn-payment" disabled style="opacity:0.6">💰 Sección Pago ▼</button>
                <div class="dropdown-content">
                    <a onclick="mostrarMensaje('realizar-pago')">💳 Realizar Pago</a>
                    <a onclick="mostrarMensaje('pago-completado')">✅ Pago Completado</a>
                </div>
            </div>
        </div>
        
        <div id="resultado" class="resultado-box"></div>
        <a href="/" class="btn-back">← Volver al inicio</a>
        
        <div id="seccionAuditoria" class="auditoria-section" style="display:none;">
            <h3>🛡️ Análisis de Vulnerabilidades</h3>
            <p style="font-size: 14px; color: #666;">Tu pago ha desbloqueado el escaneo de seguridad para <strong>{dominio}</strong></p>
            
            <button onclick="iniciarAuditoria()" id="btnAuditoria" class="btn-auditar">
                🔍 Iniciar Escaneo de Vulnerabilidades
            </button>
            
            <div id="estadoEscaneo" style="display:none; margin: 15px 0; padding: 10px; background: #f0f7ff; border-radius: 8px; color: #4a5568; font-size: 14px;"></div>
            
            <div id="resumenEscaneo" style="display:none; background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; margin: 15px 0; text-align: left;">
                <h4 style="margin-bottom: 15px; text-align: center;">📊 Resultados del Análisis para <strong>{dominio}</strong></h4>
                
                <div class="resumen-grid">
                    <div class="resumen-item resumen-criticas">
                        <span style="font-size: 24px;">🔴</span><br>
                        <strong>Críticas:</strong> <span id="countCriticas">-</span>
                    </div>
                    <div class="resumen-item resumen-medias">
                        <span style="font-size: 24px;">🟠</span><br>
                        <strong>Medias:</strong> <span id="countMedias">-</span>
                    </div>
                    <div class="resumen-item resumen-bajas">
                        <span style="font-size: 24px;">🟢</span><br>
                        <strong>Bajas:</strong> <span id="countBajas">-</span>
                    </div>
                    <div class="resumen-item" style="background: #e2e8f0;">
                        <span style="font-size: 24px;">📋</span><br>
                        <strong>Total:</strong> <span id="countTotal">-</span>
                    </div>
                </div>
                
                <h5 style="margin: 15px 0 10px 0;">🔍 Principales hallazgos:</h5>
                <ul id="listaAlertas" style="font-size: 13px; color: #4a5568; margin-bottom: 15px; padding-left: 20px;"></ul>
                
                <div style="text-align: center;">
                    <a id="linkDescarga" href="#" target="_blank" class="btn-descargar">
                        📥 Descargar Reporte Completo (HTML)
                    </a>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const email = "{email}";
        const codigo = "{codigo}";
        const dominio = "{dominio}";
        let verificado = false;
        let escaneoActivo = false;
        
        function habilitarBotonPago() {{
            const btnPago = document.getElementById('btnPago');
            btnPago.disabled = false;
            btnPago.style.opacity = '1';
        }}
        
        async function validarDNS() {{
            const btn = document.getElementById('btnValidar');
            const resultadoDiv = document.getElementById('resultado');
            
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner"></span> Verificando DNS...';
            resultadoDiv.style.display = 'block';
            resultadoDiv.className = 'resultado-box resultado-warning';
            resultadoDiv.innerHTML = '🔍 Verificando registro TXT en ' + dominio + '...';
            
            try {{
                const response = await fetch('/validar-dns', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ email: email, codigo: codigo, dominio: dominio }})
                }});
                
                const data = await response.json();
                
                if (data.exitoso) {{
                    verificado = true;
                    resultadoDiv.className = 'resultado-box resultado-success';
                    resultadoDiv.innerHTML = '✅ ' + data.mensaje;
                    habilitarBotonPago();
                }} else {{
                    resultadoDiv.className = 'resultado-box resultado-error';
                    resultadoDiv.innerHTML = '❌ ' + data.mensaje + '<br><br>💡 Espera unos minutos a que se propague el DNS y vuelve a intentar.';
                }}
            }} catch (error) {{
                resultadoDiv.className = 'resultado-box resultado-error';
                resultadoDiv.innerHTML = '❌ Error de conexión: ' + error;
            }} finally {{
                btn.disabled = false;
                btn.innerHTML = '🔍 Validar DNS';
            }}
        }}
        
        function mostrarMensaje(opcion) {{
            const resultadoDiv = document.getElementById('resultado');
            resultadoDiv.style.display = 'block';
            
            if (opcion === 'realizar-pago') {{
                resultadoDiv.className = 'resultado-box resultado-info';
                resultadoDiv.innerHTML = `
                    <strong>💰 EN DESARROLLO</strong><br><br>
                    La pasarela de pago está en fase de integración.<br><br>
                    <strong>Próximamente disponibles:</strong><br>
                    • Stripe (Tarjetas de crédito/débito)<br>
                    • PayPal<br>
                    • Transferencia bancaria<br><br>
                    <em>Por ahora, usa la opción "Pago Completado" para simular el proceso.</em>
                `;
            }} else if (opcion === 'pago-completado') {{
                resultadoDiv.className = 'resultado-box resultado-warning';
                resultadoDiv.innerHTML = '<span class="loading-spinner"></span> Procesando pago, enviando notificaciones...';
                
                fetch('/webhook-pago', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ codigo: codigo, monto: 50.00 }})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.exitoso) {{
                        resultadoDiv.className = 'resultado-box resultado-success';
                        resultadoDiv.innerHTML = `
                            <strong>✅ PAGO CONFIRMADO</strong><br><br>
                            ${{data.mensaje}}<br><br>
                            📧 Se ha enviado confirmación al administrador.<br>
                            📱 Notificación enviada por Telegram.<br>
                            🛡️ Se ha desbloqueado el <strong>Análisis de Vulnerabilidades</strong> más abajo.<br><br>
                            <em>Gracias por tu pago.</em>
                        `;
                        const opcionPago = document.querySelector('.dropdown-content a:last-child');
                        if (opcionPago) {{
                            opcionPago.style.opacity = '0.5';
                            opcionPago.style.pointerEvents = 'none';
                        }}
                        habilitarAuditoria();
                    }} else {{
                        resultadoDiv.className = 'resultado-box resultado-error';
                        resultadoDiv.innerHTML = `
                            <strong>❌ ERROR</strong><br><br>
                            ${{data.mensaje}}<br><br>
                            Por favor, contacta con soporte.
                        `;
                    }}
                }})
                .catch(error => {{
                    resultadoDiv.className = 'resultado-box resultado-error';
                    resultadoDiv.innerHTML = `
                        <strong>❌ ERROR DE CONEXIÓN</strong><br><br>
                        No se pudo procesar el pago: ${{error}}<br>
                        Intenta nuevamente.
                    `;
                }});
            }}
        }}
        
        function habilitarAuditoria() {{
            document.getElementById('seccionAuditoria').style.display = 'block';
            document.getElementById('seccionAuditoria').scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}
        
        async function iniciarAuditoria() {{
            if (escaneoActivo) {{
                alert('⚠️ Ya hay un escaneo en curso. Espera a que termine.');
                return;
            }}
            
            const btn = document.getElementById('btnAuditoria');
            const estadoDiv = document.getElementById('estadoEscaneo');
            const resumenDiv = document.getElementById('resumenEscaneo');
            
            escaneoActivo = true;
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner"></span> Iniciando escaneo...';
            estadoDiv.style.display = 'block';
            resumenDiv.style.display = 'none';
            estadoDiv.innerHTML = '⏳ Preparando contenedor ZAP...';
            
            try {{
                const response = await fetch('/lanzar-escaneo', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ email: email, dominio: dominio }})
                }});
                const data = await response.json();
                
                if (data.exitoso && data.cache) {{
                    mostrarResumen(data.resumen, data.url_completa);
                    btn.disabled = false;
                    btn.innerHTML = '🔄 Re-escanear';
                    escaneoActivo = false;
                }} else if (data.exitoso && data.escaneando) {{
                    await esperarEscaneo();
                    btn.disabled = false;
                    btn.innerHTML = '🔄 Re-escanear';
                }} else {{
                    estadoDiv.innerHTML = '❌ Error al iniciar el escaneo.';
                    btn.disabled = false;
                    btn.innerHTML = '🔍 Iniciar Escaneo de Vulnerabilidades';
                    escaneoActivo = false;
                }}
            }} catch (error) {{
                estadoDiv.innerHTML = '❌ Error de conexión: ' + error;
                btn.disabled = false;
                btn.innerHTML = '🔍 Iniciar Escaneo de Vulnerabilidades';
                escaneoActivo = false;
            }}
        }}
        
        async function esperarEscaneo() {{
            const estadoDiv = document.getElementById('estadoEscaneo');
            let intentos = 0;
            const maxIntentos = 30;
            const mensajes = [
                '🔍 Rastreando directorios y enlaces...',
                '📡 Analizando cabeceras HTTP de seguridad...',
                '🛡️ Verificando configuraciones del servidor...',
                '🔐 Comprobando cookies y políticas de seguridad...',
                '📊 Generando informe de vulnerabilidades...'
            ];
            
            while (intentos < maxIntentos) {{
                await new Promise(r => setTimeout(r, 10000));
                intentos++;
                const indiceMensaje = Math.floor(intentos / 2) % mensajes.length;
                estadoDiv.innerHTML = mensajes[indiceMensaje] + '<br><small>⏱️ Esperando ' + (intentos * 10) + ' segundos...</small>';
                
                try {{
                    const response = await fetch('/estado-escaneo', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ email: email }})
                    }});
                    const data = await response.json();
                    if (data.completado) {{
                        mostrarResumen(data.resumen, data.url_completa);
                        escaneoActivo = false;
                        return;
                    }}
                }} catch (e) {{
                    console.error('Error verificando estado:', e);
                }}
            }}
            
            estadoDiv.innerHTML = '⚠️ El escaneo está tardando más de lo esperado. Recarga la página en unos minutos.';
            escaneoActivo = false;
        }}
        
        function mostrarResumen(resumen, urlCompleta) {{
            document.getElementById('estadoEscaneo').style.display = 'none';
            
            const resumenDiv = document.getElementById('resumenEscaneo');
            resumenDiv.style.display = 'block';
            
            document.getElementById('countCriticas').innerText = resumen.criticas;
            document.getElementById('countMedias').innerText = resumen.medias;
            document.getElementById('countBajas').innerText = resumen.bajas;
            document.getElementById('countTotal').innerText = resumen.total;
            
            const lista = document.getElementById('listaAlertas');
            if (resumen.detalles.length > 0) {{
                lista.innerHTML = resumen.detalles.map(d => {{
                    const icono = d.riesgo === '3' ? '🔴' : d.riesgo === '2' ? '🟠' : d.riesgo === '1' ? '🟢' : 'ℹ️';
                    return `<li>${{icono}} <strong>${{d.nombre}}</strong></li>`;
                }}).join('');
            }} else {{
                lista.innerHTML = '<li>✅ No se detectaron vulnerabilidades.</li>';
            }}
            
            document.getElementById('linkDescarga').href = urlCompleta;
            
            resumenDiv.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}
    </script>
</body>
</html>"""
