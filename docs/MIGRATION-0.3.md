# Migrating 0.2.2 to 0.3.0

The endpoint and request shape are unchanged. Application/image and response schema_version are
0.3.0; meta.profile is workflow-premise-map-v0.3.

Care execution_effect changes from generated text to server-supplied null, meaning not assessed.
Consumers must accept null and read the goal or constraint from Care.statement, with its evidence.
For differences and implications of an AI proposal, use View. Fact/View execution_effect remains
text. The whole Care collection can still be null when no concern is known.

The internal model schema omits Care execution_effect. An emitted field returns HTTP 502 with
provider_unexpected_care_effect. The server does not erase generated content or turn a rejected
draft into a successful map. No extra model call, retry, keyword filter, or Core revision is added.

The change targets the observed unsolicited replacement suggestion in English 0.2.2 responses.
It cannot guarantee that a model will not invent a replacement elsewhere. Review all generated
fields, including statements, hypotheses, and effects in Fact/View. The earlier intermittent
Japanese quote mismatch remains unresolved; a later successful run did not explain that failure.

After applying the update, keep the existing .env and run docker compose up --build -d.
Then run the English and Japanese examples sequentially and review ACCEPTANCE.md.
