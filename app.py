from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import sqlite3
import os
from datetime import datetime
import csv
import io

class QuizRequestHandler(SimpleHTTPRequestHandler):
    
    def __init__(self, *args, **kwargs):
        self.init_database()
        super().__init__(*args, **kwargs)
    
    def init_database(self):
        """Initialize SQLite database"""
        self.conn = sqlite3.connect('quiz_database.db', check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                class TEXT NOT NULL,
                answers TEXT NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                completed_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        print("Database initialized successfully!")
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/api/participants':
            self.get_participants()
        elif self.path == '/api/statistics':
            self.get_statistics()
        elif self.path == '/api/export':
            self.export_data()
        else:
            # Serve static files
            super().do_GET()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/participants':
            self.add_participant()
        else:
            self.send_error(404)
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        if self.path == '/api/participants':
            self.delete_participants()
        else:
            self.send_error(404)
    
    def get_participants(self):
        """Get all participants"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT name, email, class, answers, score, total_questions, completed_at
                FROM participants 
                ORDER BY completed_at DESC
                LIMIT 50
            ''')
            
            participants = []
            for row in cursor.fetchall():
                participants.append({
                    'name': row[0],
                    'email': row[1],
                    'class': row[2],
                    'answers': eval(row[3]),
                    'score': row[4],
                    'total_questions': row[5],
                    'completed_at': row[6]
                })
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(participants).encode())
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def add_participant(self):
        """Add new participant"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO participants (name, email, class, answers, score, total_questions, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['name'],
                data['email'],
                data['class'],
                str(data['answers']),
                data['score'],
                data['total_questions'],
                data['completed_at']
            ))
            
            self.conn.commit()
            
            self.send_response(201)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'message': 'Participant added successfully'}).encode())
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def get_statistics(self):
        """Get quiz statistics"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM participants')
            total_participants = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(score) FROM participants WHERE score IS NOT NULL')
            avg_score = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM participants WHERE score = 3')
            perfect_scores = cursor.fetchone()[0]
            
            stats = {
                'total_participants': total_participants,
                'average_score': round(float(avg_score), 1),
                'perfect_scores': perfect_scores
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode())
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def export_data(self):
        """Export data as CSV"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT name, email, class, score, total_questions, completed_at
                FROM participants 
                ORDER BY completed_at DESC
            ''')
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Nama', 'Email', 'Kelas/Instansi', 'Skor', 'Total Pertanyaan', 'Waktu Selesai'])
            
            for row in cursor.fetchall():
                writer.writerow(row)
            
            csv_data = output.getvalue()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/csv')
            self.send_header('Content-Disposition', f'attachment; filename="data_peserta_quiz_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(csv_data.encode())
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def delete_participants(self):
        """Delete all participants"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM participants')
            self.conn.commit()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'message': 'All participants deleted successfully'}).encode())
            
        except Exception as e:
            self.send_error(500, str(e))

def run_server():
    """Run the HTTP server"""
    port = 8000
    server_address = ('', port)
    httpd = HTTPServer(server_address, QuizRequestHandler)
    
    print(f"Server berjalan di http://localhost:{port}")
    print("Buka browser dan akses http://localhost:8000")
    print("Tekan Ctrl+C untuk menghentikan server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan")
        httpd.server_close()

if __name__ == '__main__':
    run_server()