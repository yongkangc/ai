I am using you as a prompt generator. I've dumped the entire context of my code base, and I have a specific problem. Please come up with a proposal to my problem - including the code and general approach.

<PROBLEM>

</PROBLEM>


Please make sure that you leave no details out, and follow my requirements specifically. I know what I am doing, and you can assume that there is a reason for my arbitrary requirements.

When generating the full prompt with all of the details, keep in mind that the model you are sending this to is not as intelligent as you. It is great at very specific instructions, so please stress that they are specific.

Come up with discrete steps such that the sub-llm i am passing this to can build intermediately; as to keep it on the rails. Make sure to stress that it stops for feedback at each discrete step.