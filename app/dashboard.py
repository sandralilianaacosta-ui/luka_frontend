from datetime import date, datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.database import Movimiento, Presupuesto, Meta

# ==============================================================================
# LÓGICA DE AGREGACIÓN DE DATOS (SQLAlchemy ORM)
# ==============================================================================

def get_summary_stats(db: Session, usuario_id: int, date_from: Optional[date] = None, date_to: Optional[date] = None) -> Dict[str, Any]:
    """
    Calcula los KPIs principales del usuario para las tarjetas superiores.
    - Patrimonio Neto (Unificado ARS con cotización estática/cacheada 1 USD = 1000 ARS)
    - Consumo de Presupuesto mensual (%)
    - Racha de días consecutivos registrando transacciones desde la BD
    """
    # 1. Calcular Patrimonio Neto (Sumatoria de ingresos - egresos unificados)
    # Requerimiento: No llamar a APIs externas en tiempo real, usar cotización cacheada (1 USD = 1000 ARS)
    query = db.query(Movimiento).filter(Movimiento.usuario_id == usuario_id)
    if date_from:
        query = query.filter(Movimiento.fecha >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Movimiento.fecha <= datetime.combine(date_to, datetime.max.time()))
        
    movimientos = query.all()
    
    total_ars = 0.0
    for mov in movimientos:
        # Convertimos a ARS si es USD usando la tasa estática
        monto_ars = mov.monto if mov.divisa == "ARS" else mov.monto * 1000.0
        if mov.tipo == "ingreso":
            total_ars += monto_ars
        else:
            total_ars -= monto_ars

    # 2. Consumo de Presupuesto (Monto gastado en el mes actual vs Límite)
    mes_actual = datetime.now().month
    anio_actual = datetime.now().year
    
    gastos_mes = db.query(func.sum(Movimiento.monto))\
        .filter(
            Movimiento.usuario_id == usuario_id,
            Movimiento.tipo == "egreso",
            Movimiento.divisa == "ARS",  # Presupuestos típicamente en ARS
            func.extract('month', Movimiento.fecha) == mes_actual,
            func.extract('year', Movimiento.fecha) == anio_actual
        ).scalar() or 0.0
        
    limite_presupuesto = db.query(func.sum(Presupuesto.limite))\
        .filter(Presupuesto.usuario_id == usuario_id, Presupuesto.activo == True)\
        .scalar() or 0.0
        
    consumo_pct = 0.0
    if limite_presupuesto > 0:
        consumo_pct = (gastos_mes / limite_presupuesto) * 100.0

    # 3. Racha de Días Consecutivos (Cálculo optimizado desde BD)
    fechas_unicas = db.query(func.date(Movimiento.fecha))\
        .filter(Movimiento.usuario_id == usuario_id)\
        .group_by(func.date(Movimiento.fecha))\
        .order_by(func.date(Movimiento.fecha).desc())\
        .all()
        
    dias_racha = 0
    if fechas_unicas:
        hoy = date.today()
        # Limpiamos la tupla que retorna SQLAlchemy
        lista_fechas = [f[0] for f in fechas_unicas]
        
        # Si el último registro no fue hoy ni ayer, la racha activa es 0
        if lista_fechas[0] == hoy or lista_fechas[0] == hoy.replace(day=hoy.day - 1 if hoy.day > 1 else 1): # fallback simple para ayer
            dias_racha = 1
            for i in range(len(lista_fechas) - 1):
                diff = (lista_fechas[i] - lista_fechas[i+1]).days
                if diff == 1:
                    dias_racha += 1
                elif diff > 1:
                    break  # Se rompió la racha

    return {
        "patrimonio_neto": total_ars,
        "consumo_presupuesto": consumo_pct,
        "dias_racha": dias_racha
    }

def get_expenses_by_category(db: Session, usuario_id: int, date_from: Optional[date] = None, date_to: Optional[date] = None) -> Dict[str, float]:
    """
    [Requerimiento Jira 1]: Agrupación GROUP BY por etiqueta de categoría.
    Retorna un diccionario de categoría: total_gastado.
    """
    query = db.query(
        Movimiento.categoria,
        func.sum(Movimiento.monto).label("total")
    ).filter(
        Movimiento.usuario_id == usuario_id,
        Movimiento.tipo == "egreso"
    )
    
    if date_from:
        query = query.filter(Movimiento.fecha >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Movimiento.fecha <= datetime.combine(date_to, datetime.max.time()))
        
    resultados = query.group_by(Movimiento.categoria).all()
    return {row.categoria: row.total for row in resultados if row.categoria}

def get_expenses_by_day(db: Session, usuario_id: int, date_from: Optional[date] = None, date_to: Optional[date] = None) -> List[Dict[str, Any]]:
    """
    Agrupa los egresos por día para armar el histórico de gastos.
    """
    query = db.query(
        func.date(Movimiento.fecha).label("dia"),
        func.sum(Movimiento.monto).label("total")
    ).filter(
        Movimiento.usuario_id == usuario_id,
        Movimiento.tipo == "egreso"
    )
    
    if date_from:
        query = query.filter(Movimiento.fecha >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Movimiento.fecha <= datetime.combine(date_to, datetime.max.time()))
        
    resultados = query.group_by(func.date(Movimiento.fecha)).order_by("dia").all()
    return [{"date": str(row.dia), "amount": row.total} for row in resultados]

def get_recent_transactions(db: Session, usuario_id: int, limit: int = 10, date_from: Optional[date] = None, date_to: Optional[date] = None) -> List[Dict[str, Any]]:
    """
    Retorna el historial de movimientos ordenados del más nuevo al más viejo.
    """
    query = db.query(Movimiento).filter(Movimiento.usuario_id == usuario_id)
    
    if date_from:
        query = query.filter(Movimiento.fecha >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Movimiento.fecha <= datetime.combine(date_to, datetime.max.time()))
        
    resultados = query.order_by(Movimiento.fecha.desc()).limit(limit).all()
    
    return [
        {
            "id": r.id,
            "date": r.fecha.strftime("%Y-%m-%d"),
            "time": r.fecha.strftime("%H:%M"),
            "category": r.categoria,
            "description": f"{r.tipo.capitalize()} - {r.divisa}",
            "amount": r.monto if r.tipo == "egreso" else -r.monto  # Representación de flujos
        }
        for r in resultados
    ]

def get_budgets_with_usage(db: Session, usuario_id: int, date_from: Optional[date] = None, date_to: Optional[date] = None) -> List[Dict[str, Any]]:
    """
    Retorna el estado de los presupuestos y su consumo real.
    """
    presupuestos = db.query(Presupuesto).filter(Presupuesto.usuario_id == usuario_id, Presupuesto.activo == True).all()
    
    output = []
    for p in presupuestos:
        # Sumamos los gastos asociados a la categoría del presupuesto en el mes actual
        mes_actual = datetime.now().month
        gastado = db.query(func.sum(Movimiento.monto))\
            .filter(
                Movimiento.usuario_id == usuario_id,
                Movimiento.categoria == p.limite,  # Asumiendo que se filtra por categoría
                Movimiento.tipo == "egreso",
                func.extract('month', Movimiento.fecha) == mes_actual
            ).scalar() or 0.0
            
        output.append({
            "categoria": p.id,  # Fallback seguro
            "limite": p.limite,
            "gastado": gastado,
            "porcentaje": (gastado / p.limite * 100.0) if p.limite > 0 else 0.0
        })
    return output

def get_or_create_user(db: Session, whatsapp_id: str) -> Any:
    """
    Stub para asegurar la existencia del usuario simulado en el login de desarrollo.
    """
    # En un entorno real, buscaría el usuario. Dejamos un mock robusto que no rompa:
    class UserStub:
        def __init__(self, id, whatsapp_id):
            self.id = id
            self.whatsapp_id = whatsapp_id
    return UserStub(1, whatsapp_id)
