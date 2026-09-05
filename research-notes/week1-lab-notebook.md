# ZTDS-CC Week 1 Research Lab Notebook

## Day 1 — Nitro Enclave Environment Validation

### Objective

Validate an AWS Nitro Enclaves parent instance and successfully:

1. install the Nitro CLI;
2. allocate enclave CPU and memory;
3. build an Enclave Image File (EIF);
4. launch an enclave;
5. inspect its running state;
6. terminate it cleanly.

### Environment

- Cloud: AWS
- Parent OS: Amazon Linux 2023
- Architecture: x86_64
- Nitro Enclaves: Enabled
- Instance type:
- Region:
- Nitro CLI version:
- Docker version:
- Git commit:

### Day 1 Results

Day 1 environment validation completed successfully.

The Nitro Enclaves parent instance was launched on an AWS c6i.xlarge
instance running Amazon Linux 2023. Nitro Enclaves support was enabled
at launch.

The Nitro CLI and Docker services were installed and validated. The
enclave allocator reserved 2 vCPUs and 512 MiB of memory for enclave
execution.

The AWS Hello Enclaves example was successfully packaged as a Docker
image and converted into an Enclave Image File (EIF), `hello.eif`.

The EIF produced the following SHA-384 measurements:

- PCR0:
  `b132343d712a716a0202c9cffc40d6ae0f28ffb0d11451c476a8650b564164d70e07da5a4290101fcd70b14572e6e54c`

- PCR1:
  `4b4d5b3661b3efc12920900c80e126e4ce783c522de6c02a2a5bf7af3a2b9327b868776f188e4be1c1c404a129dbda493`

- PCR2:
  `cd96427de23b32310dfc5b14d814b6cb54d69eb71b6952b4c6785bf115d24df586c6c7a0a5290bf938dd0c7d60c666e22e`

A debug-mode enclave was then launched successfully with CID 16,
2 vCPUs, and 512 MiB RAM.

The enclave console produced repeated:

`Hello from the enclave side!`

messages, confirming successful execution inside the Nitro Enclave.

The enclave was subsequently terminated cleanly, and a final
`nitro-cli describe-enclaves` returned an empty list (`[]`).

### Day 1 Conclusion

The AWS Nitro Enclaves execution environment is operational and ready
for the next stage of the ZTDS confidential-computing testbed.

This experiment establishes the basic enclave lifecycle required for
the proposed architecture:

1. deterministic EIF construction;
2. enclave measurement generation;
3. isolated enclave execution;
4. enclave lifecycle management.

The next milestone is to replace the simple Hello Enclaves workload
with a parent-to-enclave vsock communication path and begin constructing
the attestation-verification workflow.