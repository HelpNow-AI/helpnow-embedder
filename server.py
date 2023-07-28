import argparse
import logging

import numpy as np
from sentence_transformers import SentenceTransformer

from pytriton.decorators import batch
from pytriton.model_config import ModelConfig, Tensor
from pytriton.triton import Triton

from _config import logger

logger.info("🔥 bb8-embedder by Triton Inferece Server")


## Load models
# nlu_embedder = SentenceTransformer('./transformer-models/nlu-sentence-embedder', device='cpu')
nlu_embedder = SentenceTransformer('bespin-global/klue-sroberta-base-continue-learning-by-mnr', device='cpu')
# pool = nlu_embedder.start_multi_process_pool()

# assist_embedder = SentenceTransformer('./transformer-models/assist-sentence-embedder', device='cpu')
assist_bi_encoder = SentenceTransformer('sentence-transformers/multi-qa-mpnet-base-dot-v1', device='cpu')
# pool = assist_embedder.start_multi_process_pool()


@batch
def _infer_fn_nlu(sequence: np.ndarray):
    sequence = np.char.decode(sequence.astype("bytes"), "utf-8")  # need to convert dtype=object to bytes first
    sequence = sum(sequence.tolist(), [])

    embed_vectors = nlu_embedder.encode(sequence)

    return {'embed_vectors': embed_vectors}

@batch
def _infer_fn_assist(sequence: np.ndarray):
    sequence = np.char.decode(sequence.astype("bytes"), "utf-8")  # need to convert dtype=object to bytes first
    sequence = sum(sequence.tolist(), [])

    embed_vectors = assist_bi_encoder.encode(sequence)

    return {'embed_vectors': embed_vectors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-batch-size",
        type=int,
        default=10000,
        help="Batch size of request.",
        required=False,
    )
    args = parser.parse_args()


    with Triton() as triton:
        logger.info("Loading embedding model.")
        triton.bind(
            model_name="bb8-embedder-nlu",
            infer_func=_infer_fn_nlu,
            inputs=[
                Tensor(name="sequence", dtype=bytes, shape=(1,)),
            ],
            outputs=[
                Tensor(name="embed_vectors", dtype=bytes, shape=(-1,)),
            ],
            config=ModelConfig(max_batch_size=args.max_batch_size),
        )
        triton.bind(
            model_name="bb8-embedder-assist",
            infer_func=_infer_fn_assist,
            inputs=[
                Tensor(name="sequence", dtype=bytes, shape=(1,)),
            ],
            outputs=[
                Tensor(name="embed_vectors", dtype=bytes, shape=(-1,)),
            ],
            config=ModelConfig(max_batch_size=args.max_batch_size),
        )
        logger.info("Serving inference")
        triton.serve()


if __name__ == "__main__":
    main()