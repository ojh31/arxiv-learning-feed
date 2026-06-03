APP   := arxiv-learning-feed
IMAGE := ghcr.io/alignmentresearch/$(APP)
MSG   ?= Deploy $(APP)

.PHONY: deploy push build rollout verify run-now

deploy: push build rollout verify

push:
	git add -A
	@git diff --cached --quiet || git commit -m "$(MSG)"
	git push origin main || { git pull --rebase origin main && git push origin main; }

build:
	@docker info >/dev/null 2>&1 || (open -a Docker && until docker info >/dev/null 2>&1; do sleep 1; done)
	docker build --platform linux/amd64 -t $(IMAGE):latest .
	docker push $(IMAGE):latest

# CronJob picks up :latest on its next scheduled run — applying the manifest is enough.
rollout:
	kubectl apply -f k8s/cronjob.yaml

verify:
	kubectl get cronjob $(APP)

# Optional: run immediately instead of waiting for the schedule (only if asked).
run-now:
	kubectl create job --from=cronjob/$(APP) $(APP)-manual-$$(date +%s)
