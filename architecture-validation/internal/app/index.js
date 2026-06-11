const express = require('express');
const mysql = require('mysql2/promise');
const redis = require('redis');

const app = express();
const PORT = 3000;

// 1. MariaDB 연결 설정 (시방서 내부망 명세 기준)
// Write 전용 마스터 DB
const writeDbConfig = {
  host: 'db-data', 
  user: 'root',
  password: 'your_secure_root_password',
  database: 'userdb_backup'
};

// Read 전용 백업 DB (CQRS 구조)
const readDbConfig = {
  host: 'db-backup',
  user: 'root',
  password: 'your_secure_root_password',
  database: 'userdb_backup'
};

// 2. Redis 연결 설정 (cacheDB 컨테이너 환경)
const redisClient = redis.createClient({
  url: 'redis://cacheDB:6379'
});
redisClient.on('error', (err) => console.error('Redis 연결 에러:', err));

async function initServer() {
  // Redis 연결 실행
  await redisClient.connect();
  console.log('✅ Redis Cache 서버 연결 성공');

  // 데이터베이스 초기 테이블 세팅 (마스터 DB에서 실행)
  try {
    const connection = await mysql.createConnection(writeDbConfig);
    await connection.query(`
      CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(50) NOT NULL,
        role VARCHAR(20) NOT NULL
      )
    `);
    await connection.end();
    console.log('✅ MariaDB 초기화 완료 (users 테이블 확인)');
  } catch (err) {
    console.error('❌ MariaDB 초기화 실패:', err.message);
  }
}

// [기능 1] 헬스체크 및 메인 화면
app.get('/', (req, res) => {
  res.send('<h1>통합 WAS 서버 정상 작동 중 🚀</h1><p>내부 격리망(priv-net)에서 안전하게 통신하고 있습니다.</p>');
});

// [기능 2] 데이터 쓰기 요청 (CQRS - Write-Only db-data 인스턴스로 라우팅)
app.get('/add-user', async (req, res) => {
  const { name, role } = req.query; // 예시: /add-user?name=홍길동&role=고객
  if (!name || !role) {
    return res.status(400).send('name과 role 파라미터가 필요합니다.');
  }

  try {
    const connection = await mysql.createConnection(writeDbConfig);
    const [result] = await connection.execute(
      'INSERT INTO users (name, role) VALUES (?, ?)',
      [name, role]
    );
    await connection.end();

    res.json({ success: true, message: '마스터 DB 데이터 삽입 성공', insertId: result.insertId });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// [기능 3] 데이터 읽기 요청 (CQRS & Caching)
// 1차로 Redis 캐시 조회 -> 없으면 2차로 Read-Only db-backup 인스턴스에서 조회 후 캐싱
app.get('/users', async (req, res) => {
  const cacheKey = 'user_list';

  try {
    // 1. Redis 캐시 확인
    const cachedData = await redisClient.get(cacheKey);
    if (cachedData) {
      return res.json({ source: 'Redis Cache (캐시 히트!)', data: JSON.parse(cachedData) });
    }

    // 2. 캐시에 없으면 Read 전용 슬레이브 DB 조회
    const connection = await mysql.createConnection(readDbConfig);
    const [rows] = await connection.execute('SELECT * FROM users');
    await connection.end();

    // 3. 조회한 데이터를 Redis에 30초간 임시 캐싱 (TTL 설정)
    await redisClient.setEx(cacheKey, 30, JSON.stringify(rows));

    res.json({ source: 'Read-Only Backup DB (쿼리 실행)', data: rows });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// 서버 가동 및 초기화
app.listen(PORT, async () => {
  console.log(`Server is running on port ${PORT}`);
  await initServer();
});
