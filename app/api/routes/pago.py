from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from app.config import ARCHIVO_PENDIENTES
from app.services.telegram_service import enviar_notificacion_pago_telegram
import json
from datetime import datetime

router = APIRouter()


@router.get("/pago/{codigo}", response_class=HTMLResponse)
async def pagina_pago(codigo: str):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pago - klbrs.es</title>
        <meta charset="UTF-8">
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
            .container {{
                background: white;
                border-radius: 20px;
                padding: 40px;
                max-width: 550px;
                width: 100%;
                text-align: center;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }}
            .monto {{ font-size: 48px; color: #28a745; font-weight: bold; margin: 20px 0; }}
            .codigo {{
                background: #2d3748; color: #68d391; font-family: monospace;
                padding: 15px; border-radius: 8px; margin: 20px 0; word-break: break-all; font-size: 14px;
            }}
            .button-group {{ display: flex; gap: 15px; margin: 25px 0; flex-wrap: wrap; justify-content: center; }}
            .btn-pagar {{
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                color: white; padding: 14px 24px; border: none; border-radius: 10px;
                font-size: 16px; font-weight: 600; cursor: pointer; flex: 1; min-width: 180px;
            }}
            .btn-completado {{
                background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
                color: white; padding: 14px 24px; border: none; border-radius: 10px;
                font-size: 16px; font-weight: 600; cursor: pointer; flex: 1; min-width: 180px;
            }}
            .btn-back {{
                background: #6c757d; color: white; padding: 12px 24px; border: none;
                border-radius: 10px; text-decoration: none; display: inline-block; margin-top: 10px;
            }}
            .btn-pagar:hover, .btn-completado:hover {{ transform: translateY(-2px); }}
            .btn-pagar:disabled, .btn-completado:disabled {{ opacity: 0.6; cursor: not-allowed; }}
            .resultado-box {{ margin-top: 20px; padding: 15px; border-radius: 10px; display: none; }}
            .resultado-success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .resultado-warning {{ background: #fff3cd; color: #856404; border: 1px solid #ffeeba; }}
            .resultado-info {{ background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }}
            .loading-spinner {{
                display: inline-block; width: 20px; height: 20px;
                border: 3px solid rgba(255,255,255,0.3); border-radius: 50%;
                border-top-color: white; animation: spin 0.8s linear infinite;
                margin-right: 8px; vertical-align: middle;
            }}
            @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
            .badge {{
                display: inline-block; background: #ffc107; color: #856404;
                padding: 5px 12px; border-radius: 20px; font-size: 12px; margin-bottom: 15px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="badge">💰 MODO DESARROLLO - PAGO SIMULADO</div>
            <h1>💰 Sección de Pago</h1>
            <p>Dominio verificado correctamente ✅</p>
            <div class="monto">$50 USD</div>
            <div class="codigo"><strong>Código de referencia:</strong><br>{codigo}</div>
            <h3>Datos para transferencia</h3>
            <p>Banco: [TU BANCO]<br>Cuenta: [TU CUENTA]<br>Titular: [TU NOMBRE]<br>Concepto: <strong>{codigo}</strong></p>
            <hr style="margin:20px 0; border:none; border-top:1px solid #e0e0e0;">
            <h3>Opciones de pago</h3>
            <div class="button-group">
                <button onclick="realizarPago()" id="btnPagar" class="btn-pagar">💳 Realizar Pago</button>
                <button onclick="simularPagoCompletado()" id="btnCompletado" class="btn-completado">✅ Pago Completado</button>
            </div>
            <div id="resultado" class="resultado-box"></div>
            <a href="/" class="btn-back">← Volver al inicio</a>
        </div>
        <script>
            const codigo = "{codigo}";
            let temporizadorActivo = false;
            let intervalId = null;
            let tiempoRestante = 0;
            
            function mostrarResultado(tipo, mensaje) {{
                const div = document.getElementById('resultado');
                div.style.display = 'block';
                div.className = 'resultado-box resultado-' + tipo;
                div.innerHTML = mensaje;
            }}
            
            async function realizarPago() {{
                const btn = document.getElementById('btnPagar');
                btn.disabled = true;
                btn.innerHTML = '<span class="loading-spinner"></span> Redirigiendo...';
                mostrarResultado('info', '🔄 Redirigiendo a la pasarela de pago... (Modo desarrollo)');
                setTimeout(() => {{
                    mostrarResultado('info', '<strong>💰 EN DESARROLLO</strong><br><br>Usa el botón <strong>"Pago Completado"</strong> para simular.');
                    btn.disabled = false;
                    btn.innerHTML = '💳 Realizar Pago';
                }}, 2000);
            }}
            
            async function simularPagoCompletado() {{
                if (temporizadorActivo) {{ mostrarResultado('warning', '⚠️ Ya hay un proceso en curso.'); return; }}
                const btnC = document.getElementById('btnCompletado');
                const btnP = document.getElementById('btnPagar');
                tiempoRestante = 2;
                temporizadorActivo = true;
                btnC.disabled = true;
                btnP.disabled = true;
                mostrarResultado('info', '<strong>🔄 Verificando pago...</strong><br>⏱️ Tiempo restante: <span id="contador">2</span> segundos');
                intervalId = setInterval(() => {{
                    tiempoRestante--;
                    const c = document.getElementById('contador');
                    if (c) c.textContent = tiempoRestante;
                    if (tiempoRestante <= 0) {{ clearInterval(intervalId); finalizarPago(); }}
                }}, 1000);
            }}
            
            async function finalizarPago() {{
                mostrarResultado('info', '<span class="loading-spinner"></span> Enviando notificación...');
                try {{
                    const r = await fetch('/webhook-pago', {{
                        method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ codigo: codigo }})
                    }});
                    const d = await r.json();
                    if (d.exitoso) {{
                        mostrarResultado('success', '<strong>✅ PAGO CONFIRMADO</strong><br><br>' + d.mensaje);
                        document.getElementById('btnCompletado').disabled = true;
                        document.getElementById('btnPagar').disabled = true;
                    }} else {{
                        mostrarResultado('warning', '<strong>⚠️ Error:</strong> ' + d.mensaje);
                        document.getElementById('btnCompletado').disabled = false;
                        document.getElementById('btnPagar').disabled = false;
                    }}
                }} catch(e) {{
                    mostrarResultado('warning', '<strong>⚠️ Error de conexión</strong>');
                }} finally {{ temporizadorActivo = false; }}
            }}
        </script>
    </body>
    </html>
    """


@router.post("/webhook-pago")
async def webhook_pago(request: Request):
    data = await request.json()
    codigo = data.get("codigo")
    monto = data.get("monto", 50.00)
    
    try:
        with open(ARCHIVO_PENDIENTES, "r") as f:
            pendientes = json.load(f)
    except:
        pendientes = {}
    
    usuario_encontrado = None
    email_encontrado = None
    
    for email, datos in pendientes.items():
        if datos.get("codigo") == codigo:
            usuario_encontrado = datos
            email_encontrado = email
            break
    
    if not usuario_encontrado:
        return {"exitoso": False, "mensaje": "Código no encontrado"}
    
    if usuario_encontrado.get("pagado", False):
        return {"exitoso": True, "mensaje": "Este pago ya había sido confirmado anteriormente"}
    
    pendientes[email_encontrado]["pagado"] = True
    pendientes[email_encontrado]["fecha_pago"] = datetime.now().isoformat()
    
    with open(ARCHIVO_PENDIENTES, "w") as f:
        json.dump(pendientes, f, indent=2, ensure_ascii=False)
    
    with open("pagos_registrados.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | {email_encontrado} | {usuario_encontrado['nombre']} | {usuario_encontrado['apellido']} | CODIGO: {codigo} | MONTO: ${monto}\n")
    
    # Notificación Telegram
    try:
        from app.services.telegram_service import enviar_notificacion_pago_telegram
        enviar_notificacion_pago_telegram(usuario_encontrado, codigo, monto)
    except Exception as e:
        print(f"Error enviando Telegram: {e}")
    
    return {
        "exitoso": True,
        "mensaje": f"Pago confirmado correctamente. Monto: ${monto}. Nos pondremos en contacto contigo pronto."
    }
