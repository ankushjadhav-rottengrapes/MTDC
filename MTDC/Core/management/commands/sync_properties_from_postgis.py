import re

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from Core.models import Property


IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
LEADING_NUMBER_RE = re.compile(r"^\s*\d+[\s_.-]+")
KMZ_SUFFIX_RE = re.compile(r"\s+kmz\s*$", re.IGNORECASE)


def validate_identifier(value, label):
    if not IDENTIFIER_RE.match(value):
        raise CommandError(f"Invalid {label}: {value!r}")
    return value


def quote_identifier(value):
    return connection.ops.quote_name(value)


def clean_property_name(value):
    name = str(value or "").strip()
    name = LEADING_NUMBER_RE.sub("", name)
    name = KMZ_SUFFIX_RE.sub("", name).strip()
    return name.replace("_", " ").strip()


class Command(BaseCommand):
    help = (
        "Sync distinct properties from an existing PostGIS table into the "
        "Django Property master table."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--schema",
            default="public",
            help="PostGIS schema containing the source layer table. Default: public",
        )
        parser.add_argument(
            "--table",
            default="area_mtdc",
            help="PostGIS source table/layer name. Default: area_mtdc",
        )
        parser.add_argument(
            "--property-id-field",
            default="property_id",
            help="Source field containing the property ID. Default: property_id",
        )
        parser.add_argument(
            "--name-field",
            default="name",
            help="Source field containing the property name. Default: name",
        )
        parser.add_argument(
            "--fallback-name-field",
            action="append",
            default=["layer"],
            help=(
                "Fallback source field for names when --name-field is blank. "
                "Can be used multiple times. Default: layer"
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without writing to the database.",
        )
        parser.add_argument(
            "--no-update-names",
            action="store_true",
            help="Create missing properties but do not update existing names.",
        )
        parser.add_argument(
            "--deactivate-missing",
            action="store_true",
            help=(
                "Mark active Django properties as inactive when their property_id "
                "is not present in the source table. Does not delete records."
            ),
        )

    def handle(self, *args, **options):
        schema = validate_identifier(options["schema"], "schema")
        table = validate_identifier(options["table"], "table")
        property_id_field = validate_identifier(
            options["property_id_field"],
            "property ID field",
        )
        name_field = validate_identifier(options["name_field"], "name field")
        fallback_name_fields = [
            validate_identifier(field, "fallback name field")
            for field in options["fallback_name_field"]
        ]
        dry_run = options["dry_run"]
        update_names = not options["no_update_names"]
        deactivate_missing = options["deactivate_missing"]

        rows = self.fetch_source_properties(
            schema=schema,
            table=table,
            property_id_field=property_id_field,
            name_field=name_field,
            fallback_name_fields=fallback_name_fields,
        )

        if not rows:
            self.stdout.write(self.style.WARNING("No source properties found."))
            return

        created_count = 0
        updated_count = 0
        unchanged_count = 0
        skipped_count = 0
        source_property_ids = set()

        with transaction.atomic():
            for property_id, name in rows:
                if property_id is None:
                    skipped_count += 1
                    continue

                try:
                    normalized_property_id = int(property_id)
                except (TypeError, ValueError):
                    skipped_count += 1
                    self.stderr.write(
                        self.style.WARNING(
                            f"Skipping non-integer property_id: {property_id!r}"
                        )
                    )
                    continue

                if normalized_property_id <= 0:
                    skipped_count += 1
                    self.stderr.write(
                        self.style.WARNING(
                            f"Skipping non-positive property_id: {normalized_property_id}"
                        )
                    )
                    continue

                normalized_name = clean_property_name(name)
                if not normalized_name:
                    normalized_name = f"Property {normalized_property_id}"

                source_property_ids.add(normalized_property_id)
                property_obj = Property.objects.filter(
                    property_id=normalized_property_id
                ).first()

                if property_obj is None:
                    created_count += 1
                    self.stdout.write(
                        f"Create Property {normalized_property_id}: {normalized_name}"
                    )
                    if not dry_run:
                        Property.objects.create(
                            property_id=normalized_property_id,
                            name=normalized_name,
                            is_active=True,
                        )
                    continue

                changed_fields = []
                original_name = property_obj.name
                if update_names and property_obj.name != normalized_name:
                    property_obj.name = normalized_name
                    changed_fields.append("name")

                if not property_obj.is_active:
                    property_obj.is_active = True
                    changed_fields.append("is_active")

                if changed_fields:
                    updated_count += 1
                    if "name" in changed_fields:
                        self.stdout.write(
                            f"Update Property {normalized_property_id}: "
                            f"{original_name} -> {normalized_name}"
                        )
                    else:
                        self.stdout.write(
                            f"Update Property {normalized_property_id}: "
                            f"{', '.join(changed_fields)}"
                        )
                    if not dry_run:
                        property_obj.save(update_fields=[*changed_fields, "updated_at"])
                else:
                    unchanged_count += 1

            deactivated_count = 0
            if deactivate_missing:
                missing_queryset = Property.objects.filter(is_active=True).exclude(
                    property_id__in=source_property_ids
                )
                deactivated_count = missing_queryset.count()
                if deactivated_count:
                    self.stdout.write(
                        f"Deactivate {deactivated_count} properties missing from source."
                    )
                    if not dry_run:
                        missing_queryset.update(is_active=False)

            if dry_run:
                transaction.set_rollback(True)

        message = (
            f"Sync complete: {created_count} created, {updated_count} updated, "
            f"{unchanged_count} unchanged, {skipped_count} skipped"
        )
        if deactivate_missing:
            message += f", {deactivated_count} deactivated"
        if dry_run:
            message += " (dry run)"

        self.stdout.write(self.style.SUCCESS(message))

    def fetch_source_properties(
        self,
        schema,
        table,
        property_id_field,
        name_field,
        fallback_name_fields,
    ):
        source_table = (
            f"{quote_identifier(schema)}.{quote_identifier(table)}"
        )
        property_id_column = quote_identifier(property_id_field)
        name_columns = [name_field, *fallback_name_fields]
        name_expression = "COALESCE(" + ", ".join(
            f"MIN(NULLIF(BTRIM({quote_identifier(field)}::text), ''))"
            for field in name_columns
        ) + ", '')"
        query = f"""
            SELECT
                {property_id_column},
                {name_expression}
            FROM {source_table}
            WHERE {property_id_column} IS NOT NULL
            GROUP BY {property_id_column}
            ORDER BY {property_id_column}
        """

        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as exc:
            raise CommandError(
                "Could not read source properties from PostGIS. "
                "Check the schema, table, and field names."
            ) from exc
