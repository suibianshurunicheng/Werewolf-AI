from train_qlora import main

if __name__ == "__main__":
    main(default_config="configs/lora_classic.yaml", expected_quantized=False)
