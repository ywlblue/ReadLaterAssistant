from storage import connect


def oneoff_backfill():
    conn = connect()
    cursor = conn.execute("UPDATE saved_items "
                          "SET saved_at_origin = CASE "
                          "WHEN saved_at >= '2026-10-20T03' THEN 'IMPORT' "
                          "ELSE 'LIVE' "
                          "END "
                          "WHERE saved_at_origin IS NULL;"
                          )
    conn.commit()
    print(cursor.rowcount)


if __name__ == '__main__':
    oneoff_backfill()
