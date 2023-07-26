from playhouse.migrate import migrate, SchemaMigrator

def upgrade(migrator: SchemaMigrator):
    migrate(
        migrator.rename_column("randommapstogetherscore", "total_time_gained", "total_time")
    )

def downgrade(migrator: SchemaMigrator):
    migrate(
        migrator.rename_column("randommapstogetherscore", "total_time", "total_time_gained")
    )
