-- 🔄 RESET DATABASE (for development only)
DROP TABLE IF EXISTS lyrics, tracks, albums, artists, word_frequencies_album, word_frequencies_track CASCADE;

-- 🎤 ARTIST QUERIES
-- Query 1: Get all artists
SELECT * FROM artists;

-- Query 2: Search artists by name
SELECT * FROM artists WHERE name ILIKE '%Taylor%';

-- Query 3: Get artist names and genres
SELECT name, genres FROM artists;

-- 💿 ALBUM QUERIES
-- Query 4: Get all albums by a specific artist
SELECT albums.*
FROM albums
JOIN artists ON albums.artist_id = artists.id
WHERE artists.name = 'Taylor Swift';

-- Query 5: Get album names and popularity, ordered by popularity
SELECT name, popularity FROM albums
ORDER BY popularity DESC;

-- Query 6: Get unique word count per album
SELECT al.name AS album, COUNT(DISTINCT w.word) AS unique_words
FROM word_frequencies_album w
JOIN albums al ON w.album_id = al.id
GROUP BY al.name
ORDER BY unique_words DESC;

-- 🎵 TRACK QUERIES
-- Query 7: Get all tracks from a specific album
SELECT tracks.*
FROM tracks
JOIN albums ON tracks.album_id = albums.id
WHERE albums.name = '1989';

-- Query 8: Count explicit songs per artist
SELECT ar.name AS artist_name, COUNT(*) AS explicit_song_count
FROM tracks t
JOIN albums al ON t.album_id = al.id
JOIN artists ar ON al.artist_id = ar.id
WHERE t.explicit = TRUE
GROUP BY ar.name
ORDER BY explicit_song_count DESC;

-- Query 9: Get top 20 longest tracks
SELECT 
    t.name AS track_name,
    t.duration_ms,
    ar.name AS artist_name,
    al.name AS album_name
FROM tracks t
JOIN albums al ON t.album_id = al.id
JOIN artists ar ON al.artist_id = ar.id
ORDER BY t.duration_ms DESC
LIMIT 20;

-- 📝 LYRICS & TEXT ANALYSIS
-- Query 10: Get lyrics for a specific track
SELECT t.name AS track, l.text
FROM lyrics l
JOIN tracks t ON l.track_id = t.id
WHERE t.name = 'All Too Well';

-- Query 11: Get lyrics for all tracks in a specific album
SELECT 
    t.name AS track,
    l.text
FROM lyrics l
JOIN tracks t ON l.track_id = t.id
JOIN albums al ON t.album_id = al.id
WHERE al.name = 'reputation'
ORDER BY t.track_number;

-- Query 12: Get top 10 tracks with the most lines
SELECT t.name AS track, l.line_count
FROM lyrics l
JOIN tracks t ON l.track_id = t.id
ORDER BY l.line_count DESC
LIMIT 10;

-- Query 13: Get top 10 tracks with the most words
SELECT t.name AS track, l.word_count
FROM lyrics l
JOIN tracks t ON l.track_id = t.id
ORDER BY l.word_count DESC
LIMIT 10;

-- Query 14: Get tracks with low readability scores
SELECT t.name, l.readability_score
FROM lyrics l
JOIN tracks t ON l.track_id = t.id
WHERE l.readability_score < 50
ORDER BY l.readability_score ASC;

-- Query 15: Get top 10 tracks with the highest lexical density
SELECT t.name, l.lexical_density
FROM lyrics l
JOIN tracks t ON l.track_id = t.id
ORDER BY l.lexical_density DESC
LIMIT 10;

-- Query 16: Get average lexical density per album
SELECT 
    ar.name AS artist,
    al.name AS album,
    ROUND(AVG(l.lexical_density), 4) AS avg_lexical_density
FROM lyrics l
JOIN tracks t ON l.track_id = t.id
JOIN albums al ON t.album_id = al.id
JOIN artists ar ON al.artist_id = ar.id
GROUP BY ar.name, al.name
ORDER BY avg_lexical_density DESC
LIMIT 10;

-- Query 17: Rank albums by lexical density, readability, and sentiment
WITH ranked_albums AS (
    SELECT 
        ar.name AS artist,
        al.name AS album,
        ROUND(AVG(l.lexical_density)::numeric, 4) AS avg_lexical_density,
        ROUND(AVG(l.readability_score)::numeric, 2) AS avg_readability_score,
        ROUND(AVG(l.sentiment_score)::numeric, 4) AS avg_sentiment_score,
        ROW_NUMBER() OVER (
            PARTITION BY ar.name 
            ORDER BY AVG(l.lexical_density) DESC
        ) AS rank
    FROM lyrics l
    JOIN tracks t ON l.track_id = t.id
    JOIN albums al ON t.album_id = al.id
    JOIN artists ar ON al.artist_id = ar.id
    GROUP BY ar.name, al.name
)
SELECT *
FROM ranked_albums
WHERE rank <= 10
ORDER BY artist, rank;

-- Query 18: Get average lexical density per artist
SELECT ar.name AS artist, COUNT(l.track_id) AS total_tracks, AVG(l.lexical_density) AS avg_lexical_density
FROM lyrics l
JOIN tracks t ON l.track_id = t.id
JOIN albums al ON t.album_id = al.id
JOIN artists ar ON al.artist_id = ar.id
GROUP BY ar.name
ORDER BY avg_lexical_density DESC;

-- Query 19: Get average readability score per album
SELECT a.name AS album, AVG(l.readability_score) AS avg_readability
FROM lyrics l
JOIN tracks t ON l.track_id = t.id
JOIN albums a ON t.album_id = a.id
GROUP BY a.name
ORDER BY avg_readability DESC;

-- Query 20: Get top 10 tracks with the highest sentiment scores
SELECT 
    ar.name AS artist,
    al.name AS album,
    t.name AS track,
    l.sentiment_score
FROM lyrics l
JOIN tracks t ON l.track_id = t.id
JOIN albums al ON t.album_id = al.id
JOIN artists ar ON al.artist_id = ar.id
ORDER BY l.sentiment_score DESC
LIMIT 10;

-- Query 21: Get top 10 tracks with the lowest sentiment scores
SELECT 
    ar.name AS artist,
    al.name AS album,
    t.name AS track,
    l.sentiment_score
FROM lyrics l
JOIN tracks t ON l.track_id = t.id
JOIN albums al ON t.album_id = al.id
JOIN artists ar ON al.artist_id = ar.id
ORDER BY l.sentiment_score ASC
LIMIT 10;

-- 🔤 WORD FREQUENCY ANALYSIS
-- Query 22: Get top 10 most frequent words in a specific track
SELECT word, count
FROM word_frequencies_track
JOIN tracks t ON word_frequencies_track.track_id = t.id
WHERE t.name = 'Shake It Off'
ORDER BY count DESC
LIMIT 10;

-- Query 23: Get top 10 most frequent words in a specific album by a specific artist
SELECT word, count
FROM word_frequencies_album w
JOIN albums a ON w.album_id = a.id
JOIN artists ar ON w.artist_id = ar.id
WHERE a.name = '1989' AND ar.name = 'Taylor Swift'
ORDER BY count DESC
LIMIT 10;

-- Query 24: Get top 10 most frequent words across all albums by a specific artist
SELECT word, SUM(count) AS total_count
FROM word_frequencies_album w
JOIN artists ar ON w.artist_id = ar.id
WHERE ar.name = 'Taylor Swift'
GROUP BY word
ORDER BY total_count DESC
LIMIT 10;