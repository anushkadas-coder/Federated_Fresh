import flwr as fl
from typing import List, Tuple
from flwr.common import Metrics

def weighted_average(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    accuracies = [num_examples * m["accuracy"] for num_examples, m in metrics]
    examples = [num_examples for num_examples, _ in metrics]
    avg_acc = sum(accuracies) / sum(examples) if sum(examples) > 0 else 0
    print(f"\n📈 [SERVER] Global Model Accuracy Updated: {avg_acc:.4f}\n")
    return {"accuracy": avg_acc}

print("🛡️ [MASTER AGGREGATOR] Initializing Secure Federated Server...")

strategy = fl.server.strategy.FedAvg(
    fraction_fit=1.0,
    min_fit_clients=2,
    min_available_clients=2,
    evaluate_metrics_aggregation_fn=weighted_average,
)

if __name__ == "__main__":
    fl.server.start_server(
        server_address="127.0.0.1:8080",
        config=fl.server.ServerConfig(num_rounds=3),
        strategy=strategy,
    )