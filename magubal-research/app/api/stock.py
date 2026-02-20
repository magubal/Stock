"""
Stock API Endpoints
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from ..services import DataCollectionService
from ..models import get_db_connection

stock_bp = Blueprint('stock', __name__)


@stock_bp.route('/stock/<symbol>', methods=['GET'])
def get_stock_data(symbol):
    """주가 데이터 API"""
    symbol = symbol.upper()
    interval = request.args.get('interval', '1d')
    range_period = request.args.get('range', '3mo')
    
    config = current_app.config
    data_service = DataCollectionService(config)
    
    # Yahoo Finance에서 데이터 수집
    yahoo_data, yahoo_symbol = data_service.fetch_stock_data(symbol, interval, range_period)
    
    if yahoo_data:
        meta = yahoo_data.get('meta', {})
        timestamps = yahoo_data.get('timestamp', [])
        quotes = yahoo_data.get('indicators', {}).get('quote', [{}])[0]
        
        labels = [datetime.fromtimestamp(ts).strftime('%Y-%m-%d') for ts in timestamps if ts]
        prices = [quotes.get('close', [None])[i] for i in range(len(timestamps)) if timestamps[i]]
        
        current_price = prices[-1] if prices else 0
        prev_price = prices[-2] if len(prices) > 1 else current_price
        price_change = current_price - prev_price if prev_price else 0
        percent_change = (price_change / prev_price * 100) if prev_price else 0
        
        # Save to DB
        _save_stock_to_db(symbol, yahoo_data, config['DATABASE_PATH'])
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'name': meta.get('shortName', symbol),
            'currency': meta.get('currency', 'KRW'),
            'market': meta.get('exchangeName', 'Unknown'),
            'currentPrice': current_price,
            'priceChange': price_change,
            'percentChange': round(percent_change, 2),
            'labels': labels,
            'prices': prices,
            'dataSource': 'yahoo',
            'recordCount': len(prices)
        })
    else:
        return jsonify({'success': False, 'error': '종목을 찾을 수 없습니다.'}), 404


@stock_bp.route('/stocks', methods=['GET'])
def list_stocks():
    """저장된 종목 목록"""
    conn = get_db_connection(current_app.config['DATABASE_PATH'])
    cursor = conn.cursor()
    cursor.execute('SELECT symbol, name, currency, market, last_updated FROM stock_info ORDER BY last_updated DESC')
    rows = cursor.fetchall()
    conn.close()
    
    stocks = [{'symbol': r[0], 'name': r[1], 'currency': r[2], 'market': r[3], 'lastUpdated': r[4]} for r in rows]
    
    return jsonify({'success': True, 'stocks': stocks, 'count': len(stocks)})


def _save_stock_to_db(symbol, data, db_path):
    """주가 데이터 DB 저장"""
    if not data:
        return
    
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    meta = data.get('meta', {})
    timestamps = data.get('timestamp', [])
    quotes = data.get('indicators', {}).get('quote', [{}])[0]
    
    cursor.execute('''
        INSERT OR REPLACE INTO stock_info (symbol, name, currency, market, last_updated)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        symbol,
        meta.get('shortName', meta.get('symbol', symbol)),
        meta.get('currency', 'KRW'),
        meta.get('exchangeName', 'Unknown'),
        datetime.now().isoformat()
    ))
    
    for i, ts in enumerate(timestamps):
        if ts is None:
            continue
        date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO stock_prices (symbol, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol, date_str,
                quotes.get('open', [None])[i] if i < len(quotes.get('open', [])) else None,
                quotes.get('high', [None])[i] if i < len(quotes.get('high', [])) else None,
                quotes.get('low', [None])[i] if i < len(quotes.get('low', [])) else None,
                quotes.get('close', [None])[i] if i < len(quotes.get('close', [])) else None,
                quotes.get('volume', [None])[i] if i < len(quotes.get('volume', [])) else None
            ))
        except Exception:
            pass
    
    conn.commit()
    conn.close()
